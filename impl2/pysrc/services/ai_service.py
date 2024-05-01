import json
import logging
import time

import tiktoken

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
from pysrc.services.cosmos_vcore import CosmosVCore
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

            self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            self.enc = tiktoken.get_encoding("cl100k_base")
            self.model = "gpt-35-turbo"

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
            # see https://github.com/microsoft/semantic-kernel/tree/main/python
            req_settings = self.sk_kernel.get_prompt_execution_settings_from_service_id(
                "chat_completion"
            )
            req_settings.max_tokens = 2000
            req_settings.temperature = 0.7
            req_settings.top_p = 0.8
            self.html_summarize_function = self.sk_kernel.create_function_from_prompt(
                function_name="html_summarize",
                plugin_name="html_summarize",
                prompt=self.html_summarization_prompt(),
                prompt_template_settings=req_settings,
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

    def num_tokens_from_string(self, s: str) -> int:
        try:
            return len(self.encoding.encode(s))
        except Exception as e:
            logging.critical(
                "Exception in AiService#num_tokens_from_string: {}".format(str(e))
            )
            logging.exception(e, stack_info=True, exc_info=True)
            return 10000

    def generate_sparql_from_user_prompt(
        self, resp_obj: dict
    ) -> SparqlGenerationResult:
        try:
            user_prompt = resp_obj["natural_language"]
            raw_owl = resp_obj["owl"]
            owl = OwlFormatter().minimize(raw_owl)
            logging.warning(
                "AiService#generate_sparql_from_user_prompt - user_prompt: {}".format(
                    user_prompt
                )
            )
            logging.warning(
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

    async def summarize_html(self, input_html: str) -> str:
        """Use semantic kernel to summarize the given html into text"""
        return await self.sk_kernel.invoke(
            self.html_summarize_function, input_html=input_html
        )

    def text_to_chunks(self, text):
        max_chunk_size = 2048
        chunks = []
        current_chunk = ""
        for sentence in text.split("."):
            if len(current_chunk) + len(sentence) < max_chunk_size:
                current_chunk += sentence + "."
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    async def invoke_kernel(
        self,
        conversation: AiConversation,
        prompt_text,
        user_query,
        context,
        max_tokens=1000,
        temperature=0.4,
        top_p=0.5,
    ) -> AiCompletion | None:

        try:
            logging.warning(
                "AiService#invoke_kernel, user_query: {} {}".format(
                    user_query, len(user_query)
                )
            )

            # Truncate the input as necessary
            # gpt35turbo: This model's maximum context length is 8192 tokens.
            # Need to summarize the input to fit within this limit.
            context = ""  # TODO

            ntokens = self.num_tokens_from_string(user_query + context)
            logging.error("AiService#invoke_kernel - ntokens: {}".format(ntokens))

            if False:
                if ntokens > 5000:
                    pct = (float(8192) / float(ntokens)) * 0.5
                    orig_len = float(len(user_query))
                    trunc_len = int(orig_len * pct)
                    context = user_query[0:trunc_len]
                    logging.error(
                        "AiService#invoke_kernel - truncated context from {} to {}, pct: {}".format(
                            orig_len, trunc_len, pct
                        )
                    )

            # logging.warning("AiService#invoke_kernel, context:    {}".format(context))
            conversation.add_user_message(user_query)
            conversation.add_system_message(context)

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
                        name="user_query",
                        description="The user input",
                        is_required=True,
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
                self.chat_function = self.sk_kernel.create_function_from_prompt(
                    function_name="chat",
                    plugin_name="chatPlugin",
                    prompt_template_config=chat_prompt_template_config,
                )

            kernel_args = sk.KernelArguments(
                user_query=user_query,
                context=context,
                history=conversation.get_chat_history().serialize(),
            )

            invoke_result = await self.sk_kernel.invoke(self.chat_function, kernel_args)
            # invoke_result is an instance of class:
            # <class 'semantic_kernel.functions.function_result.FunctionResult'>
            # logging.info("AiService#invoke_kernel - invoke_result: {}".format(invoke_result))

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
        prompt_text = """
        ChatBot can have a conversation with you about any topic.
        It can give explicit instructions or say 'I don't know' if it does not have an answer.

        Context:
        {{$context}}
        
        Chat history:
        {{$history}}
        
        User: {{$user_query}}
        ChatBot: """
        return prompt_text

    def html_summarization_prompt(self) -> str:
        prompt_text = """
Your task is to generate a short summary of the following HTML text.

Summarize the HTML below, delimited by triple backticks, in at most 100 words. 
 
HTML: ```{{$input_html}}```
"""
        return prompt_text

    def text_summarization_tldr_prompt(self) -> str:
        prompt_text = """
{{$input_text}}

One line TLDR with the fewest words."""
        return prompt_text
