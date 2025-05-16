from maa.agent.agent_server import AgentServer
from maa.context import Context
from agent.custom.reco.typewriter import TypeWriterCodeInput

@AgentServer.custom_action("TypeWriterCodeInput.mark_success")
def mark_success(context: Context):
    TypeWriterCodeInput.mark_success()

@AgentServer.custom_action("TypeWriterCodeInput.mark_fail")
def mark_fail(context: Context):
    TypeWriterCodeInput.mark_fail()
