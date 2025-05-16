import json
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from typing import Union, Optional
from maa.define import RectType

CODE_FILE = "assets/resource/base/pipeline/typewriter_codes.json"

@AgentServer.custom_recognition("TypeWriterCodeInput")
class TypeWriterCodeInput(CustomRecognition):
    current_index = 0
    codes = []
    success_count = 0
    fail_count = 0
    failed_codes = []

    @classmethod
    def load_codes(cls):
        if not cls.codes:
            with open(CODE_FILE, "r", encoding="utf-8") as f:
                cls.codes = json.load(f)

    def analyze(self, context: Context, argv: CustomRecognition.AnalyzeArg) -> Union[CustomRecognition.AnalyzeResult, Optional[RectType]]:
        self.load_codes()
        if self.current_index < len(self.codes):
            code = self.codes[self.current_index]
            self.current_index += 1
            return {"text": code}
        else:
            context.logger.info("🎉 兑换码处理完毕")
            context.logger.info(f"✅ 成功兑换数量: {self.success_count}")
            context.logger.info(f"❌ 失败兑换数量: {self.fail_count}")
            if self.failed_codes:
                context.logger.info("以下兑换码失败（可能已兑换过）：")
                for code in self.failed_codes:
                    context.logger.info(f" - {code}")
            return {"text": "", "stop": True}

    @classmethod
    def mark_success(cls):
        cls.success_count += 1

    @classmethod
    def mark_fail(cls):
        if cls.current_index > 0:
            cls.fail_count += 1
            cls.failed_codes.append(cls.codes[cls.current_index - 1])
