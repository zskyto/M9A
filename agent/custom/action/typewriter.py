import json
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.custom_action import CustomAction
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
    printed_summary = False  # 控制打印只执行一次

    @classmethod
    def load_codes(cls, codes_path=None):
        # 每次任务开始时重置所有状态
        if codes_path is None:
            codes_path = CODE_FILE
        with open(codes_path, "r", encoding="utf-8") as f:
            cls.codes = json.load(f)
        cls.current_index = 0
        cls.success_count = 0
        cls.fail_count = 0
        cls.failed_codes = []
        cls.printed_summary = False

    def analyze(self, context: Context, argv: CustomRecognition.AnalyzeArg) -> Union[CustomRecognition.AnalyzeResult, Optional[RectType]]:
        # 第一次调用时加载兑换码列表，支持从参数读取文件路径
        if not self.codes or self.current_index == 0:
            codes_path = argv.get('codes', CODE_FILE)
            self.load_codes(codes_path)

        if self.current_index < len(self.codes):
            code = self.codes[self.current_index]
            self.current_index += 1
            return {"text": code}
        else:
            # 只打印一次兑换码总结
            if not self.printed_summary:
                self.print_summary(context)
                self.printed_summary = True
            return {"text": "", "stop": True}

    @classmethod
    def print_summary(cls, context: Context):
        context.logger.info("🎉 所有兑换码已处理完毕")
        context.logger.info(f"✅ 成功兑换数量: {cls.success_count}")
        context.logger.info(f"❌ 失败兑换数量: {cls.fail_count}")
        if cls.failed_codes:
            context.logger.info("以下兑换码失败（可能已兑换过）：")
            for code in cls.failed_codes:
                context.logger.info(f" - {code}")

    @classmethod
    def on_exit(cls, context: Context):
        # 任务被中断时调用，打印当前兑换码执行统计
        if cls.current_index > 0 and (cls.success_count > 0 or cls.fail_count > 0):
            context.logger.info("⚠️ 打字机兑奖任务被中断，已处理兑换码部分统计：")
            cls.print_summary(context)

    @classmethod
    def mark_success(cls):
        cls.success_count += 1

    @classmethod
    def mark_fail(cls):
        if cls.current_index > 0:
            cls.fail_count += 1
            cls.failed_codes.append(cls.codes[cls.current_index - 1])

@AgentServer.custom_action("TypewriterMarkSuccess")
def typewriter_mark_success(context: Context):
    TypeWriterCodeInput.mark_success()

@AgentServer.custom_action("TypewriterMarkFail")
def typewriter_mark_fail(context: Context):
    TypeWriterCodeInput.mark_fail()
