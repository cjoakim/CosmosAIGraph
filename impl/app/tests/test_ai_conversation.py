import json

from semantic_kernel.contents.chat_history import ChatHistory

from src.services.ai_conversation import AiConversation

# pytest -v tests/test_ai_conversation.py

def test_chat_history():
    """ This test just explores and verifies the SK ChatHistory functionality. """
    hist1 = ChatHistory()
    hist1.add_user_message("this is a user message")
    hist1.add_system_message("this is a system message")
    hist1.add_assistant_message("this is an assistant message")
    hist1.add_tool_message("this is an assistant message")
    jstr = hist1.serialize()
    print(jstr)
    assert len(hist1.messages) == 4

    hist2 = ChatHistory.restore_chat_history(jstr)
    assert len(hist2.messages) == 4

def test_constructor_and_messages():
    conv1 = AiConversation()
    conv1.add_user_message("this is a user message")
    conv1.add_system_message("this is a system message")
    conv1.add_assistant_message("this is an assistant message")
    conv1.add_tool_message("this is an assistant message")

    jstr = conv1.serialize()
    print(jstr)
    assert jstr is not None
    json_obj = json.loads(jstr)
    assert json_obj["conversation_id"] is not None
    assert json_obj["chat_history"] is not None
    assert len(json_obj["chat_history"]["messages"]) == 4

    conv2 = AiConversation(json_obj)
    assert conv1.get_conversation_id() == conv2.get_conversation_id()
    assert conv1.get_message_count() == conv2.get_message_count()
    assert conv2.get_message_count() == 4

    conv2.add_user_message("this is another user message")
    conv3 = AiConversation(json.loads(conv2.serialize()))
    assert conv3.get_message_count() == 5
    assert conv1.get_conversation_id() == conv3.get_conversation_id()

    print(conv3.serialize())

def test_truncate_context_and_history():
    pass
