from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import os
import re
from typing import Dict, List

@register("jm", "MeowPaw", "打标加密插件", "1.0.0")
class JMPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 用于存储用户状态的字典，键为用户ID，值为状态
        # 状态: 0 - 未开始, 1 - 等待文件
        self.user_states: Dict[str, int] = {}
        # 支持的文件后缀
        self.supported_extensions = ['.bdi', '.bds', '.bda']
        # 临时文件存储路径
        self.temp_dir = os.path.join(os.path.dirname(__file__), "temp")

    async def initialize(self):
        """插件初始化方法"""
        logger.info("打标加密插件已初始化")
        # 确保临时目录存在
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    @filter.private_message()
    async def handle_private_message(self, event: AstrMessageEvent):
        """处理私聊消息"""
        user_id = event.sender_id
        message_str = event.message_str.strip()
        
        # 如果消息是"打标加密"，则开始流程
        if message_str == "打标加密":
            self.user_states[user_id] = 1
            response = "您正在使用MeowPaw打标系统，请发送需要打标的键盘皮肤"
            yield event.plain_result(response)
            return
        
        # 如果用户处于等待文件状态，检查是否有文件
        if user_id in self.user_states and self.user_states[user_id] == 1:
            # 检查消息中是否包含文件
            files = event.get_files()
            if not files:
                yield event.plain_result("请发送键盘皮肤文件（.bdi/.bds/.bda格式）")
                return
            
            processed_files = []
            for file in files:
                # 检查文件后缀是否符合要求
                file_ext = os.path.splitext(file.filename)[1].lower()
                if file_ext not in self.supported_extensions:
                    yield event.plain_result(f"不支持的文件格式: {file.filename}，请发送.bdi/.bds/.bda格式的文件")
                    continue
                
                # 处理文件
                try:
                    # 下载文件
                    file_path = os.path.join(self.temp_dir, file.filename)
                    await file.save(file_path)
                    
                    # 重命名文件（添加JM_前缀）
                    new_filename = f"JM_{file.filename}"
                    new_file_path = os.path.join(self.temp_dir, new_filename)
                    os.rename(file_path, new_file_path)
                    
                    # 将处理后的文件发送回去
                    await event.reply_file(new_file_path)
                    processed_files.append(file.filename)
                    
                    # 处理完成后删除临时文件
                    if os.path.exists(new_file_path):
                        os.remove(new_file_path)
                except Exception as e:
                    logger.error(f"处理文件失败: {str(e)}")
                    yield event.plain_result(f"处理文件 {file.filename} 失败: {str(e)}")
            
            if processed_files:
                yield event.plain_result(f"已完成对以下文件的打标加密处理: {', '.join(processed_files)}")
                # 重置用户状态
                self.user_states[user_id] = 0
            return

    async def terminate(self):
        """插件销毁方法"""
        logger.info("打标加密插件已卸载")
        # 清理临时目录
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)