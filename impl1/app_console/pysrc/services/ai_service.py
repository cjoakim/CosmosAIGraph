import json
import logging
import time


from openai import AzureOpenAI

import semantic_kernel as sk

from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureTextEmbedding,
)
from semantic_kernel.connectors.ai.open_ai import OpenAITextPromptExecutionSettings
from semantic_kernel.prompt_template.input_variable import InputVariable

from pysrc.models.internal_models import SparqlGenerationResult
from pysrc.services.ai_completion import AiCompletion
from pysrc.services.ai_conversation import AiConversation
from pysrc.services.config_service import ConfigService
from pysrc.services.cosmos_vcore_service import CosmosVCoreService
from pysrc.util.owl_formatter import OwlFormatter
from pysrc.util.prompts import Prompts

# Instances of this class are used to execute AzureOpenAI and LangChain functionality.
# Chris Joakim, Aleksey Savateyev, Microsoft


class AiService:
    def __init__(self, opts={}):
        """
        Get the necessary environment variables and initialze an AzureOpenAI client.
        Also read the OWL file.
        """
        try:
            self.opts = opts
            self.aoai_endpoint = ConfigService.azure_openai_url()
            self.aoai_api_key = ConfigService.azure_openai_key()
            self.aoai_version = ConfigService.azure_openai_version()
            self.chat_function = None

            self.aoai_client = AzureOpenAI(
                azure_endpoint=self.aoai_endpoint,
                api_key=self.aoai_api_key,
                api_version=self.aoai_version,
            )
            self.completions_deployment = (
                ConfigService.azure_openai_completions_deployment()
            )
            self.embeddings_deployment = (
                ConfigService.azure_openai_embeddings_deployment()
            )
            self.sk_kernel = sk.Kernel()
            self.sk_kernel.add_service(
                AzureChatCompletion(
                    service_id="chat_completion",
                    deployment_name=self.completions_deployment,
                    endpoint=self.aoai_endpoint,
                    api_key=self.aoai_api_key,
                )
            )
            self.sk_kernel.add_service(
                AzureTextEmbedding(
                    service_id="text_embedding",
                    deployment_name=self.embeddings_deployment,
                    endpoint=self.aoai_endpoint,
                    api_key=self.aoai_api_key,
                )
            )
            opts = dict()
            opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
            self.vcore = CosmosVCoreService(opts)
            self.vcore.set_db(ConfigService.graph_source_db())

            logging.info("aoai endpoint:     {}".format(self.aoai_endpoint))
            logging.info("aoai version:      {}".format(self.aoai_version))
            logging.info("aoai client:  {}".format(self.aoai_client))
            logging.info(
                "aoai completions_deployment: {}".format(self.completions_deployment)
            )
            logging.info(
                "aoai embeddings_deployment:  {}".format(self.embeddings_deployment)
            )
            logging.debug("sk_kernel: {}".format(self.sk_kernel))
        except Exception as e:
            logging.critical("Exception in AiService#__init__: {}".format(str(e)))
            logging.exception(e, stack_info=True, exc_info=True)
            return None

    def generate_sparql_from_user_prompt(
        self, resp_obj: dict
    ) -> SparqlGenerationResult:
        try:
            user_prompt = resp_obj["natural_language"]
            raw_owl = resp_obj["owl"]
            owl = OwlFormatter().minimize(raw_owl)
            logging.info(
                "AiService#generate_sparql_from_user_prompt - user_prompt: {}".format(
                    user_prompt
                )
            )
            logging.info(
                "AiService#generate_sparql_from_user_prompt - owl first 80 chars: {}".format(
                    str(owl)[0:80]
                )
            )
            if self.moderate_sparql_gen_input(user_prompt, owl):
                t1 = time.perf_counter()
                system_prompt = Prompts().generate_sparql_system_prompt(owl)
                completion = self.aoai_client.chat.completions.create(
                    model=self.completions_deployment,
                    temperature=0,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                t2 = time.perf_counter()
                # completion is an instance of <class 'openai.types.chat.chat_completion.ChatCompletion'>
                # https://platform.openai.com/docs/api-reference/chat/object
                sparql = json.loads(completion.choices[0].message.content).get("SPARQL")
                resp_obj["completion_id"] = completion.id
                resp_obj["completion_model"] = completion.model
                resp_obj["prompt_tokens"] = completion.usage.prompt_tokens
                resp_obj["completion_tokens"] = completion.usage.completion_tokens
                resp_obj["total_tokens"] = completion.usage.total_tokens
                resp_obj["elapsed"] = t2 - t1
                resp_obj["sparql"] = sparql
                if resp_obj["sparql"] == None:
                    resp_obj["sparql"] = ""
                logging.info(
                    "AiService#generate_sparql_from_user_prompt - sparql: {}".format(
                        sparql
                    )
                )
            else:
                resp_obj["error"] = "content moderation failed"
        except Exception as e:
            resp_obj["error"] = str(e)
            logging.critical("Exception in create_sparql_query: {}".format(str(e)))
            logging.exception(e, stack_info=True, exc_info=True)
        return resp_obj

    def moderate_sparql_gen_input(self, user_prompt, owl):
        """Return True if the input should be processed, else return False."""
        try:
            if user_prompt == None:
                return False
            if owl == None:
                return False
            if len(user_prompt.strip()) < 10:
                return False
            if len(owl.strip()) < 10:
                return False
            return True
        except Exception as e:
            return False

    def generate_embeddings(self, text):
        """
        Generate an embeddings array from the given text.
        Return an CreateEmbeddingResponse object or None.
        Invoke 'resp.data[0].embedding' to get the array of 1536 floats.
        """
        try:
            # <class 'openai.types.create_embedding_response.CreateEmbeddingResponse'>
            return self.aoai_client.embeddings.create(
                input=text, model=self.embeddings_deployment
            )
        except Exception as e:
            logging.critical("Exception in generate_embeddings: {}".format(str(e)))
            logging.exception(e, stack_info=True, exc_info=True)
            return None

    async def invoke_kernel(
        self,
        conversation: AiConversation,
        prompt_text,
        user_text,
        context,
        max_tokens=2000,
        temperature=0.5,
        top_p=0.5,
    ) -> AiCompletion | None:

        try:
            logging.warning("invoke_kernel, user_text: {}".format(user_text))
            logging.warning("invoke_kernel, context:    {}".format(context))
            conversation.add_user_message(user_text)
            conversation.add_system_message(
                context
            )  # conversation.chat_history.serialize())

            execution_settings = OpenAITextPromptExecutionSettings(
                service_id="chat_completion",
                ai_model_id=self.completions_deployment,
                max_tokens=abs(max_tokens),
                temperature=abs(temperature),
                top_p=abs(top_p),
            )

            chat_prompt_template_config = sk.PromptTemplateConfig(
                template=prompt_text,
                name="chat",
                template_format="semantic-kernel",
                input_variables=[
                    InputVariable(
                        name="history",
                        description="The conversation ChatHistory",
                        is_required=True,
                    ),
                    InputVariable(
                        name="user_text", description="The user input", is_required=True
                    ),
                    InputVariable(
                        name="context",
                        description="RAG data to augment the LLM",
                        is_required=True,
                    ),
                ],
                execution_settings=execution_settings,
            )

            if self.chat_function is None:
                # self.chat_function = self.sk_kernel.create_function_from_prompt(
                #     prompt=prompt_text,
                #     function_name="ChatGPTFunc2",
                #     plugin_name="chatGPTPlugin2",
                #     prompt_template_config=chat_prompt_template_config)
                self.chat_function = self.sk_kernel.create_function_from_prompt(
                    function_name="chat",
                    plugin_name="chatPlugin",
                    prompt_template_config=chat_prompt_template_config,
                )

            kernel_args = sk.KernelArguments(
                user_text=user_text,
                context=context,
                history=conversation.get_chat_history().serialize(),
            )

            invoke_result = await self.sk_kernel.invoke(self.chat_function, kernel_args)

            conversation.add_assistant_message(str(invoke_result))
            completion = AiCompletion(conversation.get_conversation_id(), invoke_result)
            conversation.add_completion(completion)
            self.vcore.save_conversation(conversation)
            return completion
        except Exception as e:
            conversation.add_assistant_message("exception: {}".format(str(e)))
            logging.critical("Exception in invoke_kernel: {}".format(str(e)))
            logging.exception(e, stack_info=True, exc_info=True)
            return None

    def generic_prompt(self) -> str:
        # TODO - possibly refactor this perhaps into an AiPrompts class
        prompt_text = """
        ChatBot can have a conversation with you about any topic.
        It can give explicit instructions or say 'I don't know' if it does not have an answer.

        Context:
        {{$context}}
        
        Chat history:
        {{$history}}
        
        User: {{$user_text}}
        ChatBot: """
        return prompt_text
