from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType
from app.utils.http import RequestUtils
from typing import Any, List, Dict, Tuple
from app.log import logger


class Gotify(_PluginBase):
    # 插件名称
    plugin_name = "Gotify"
    # 插件描述
    plugin_desc = "事件发生时向Gotify发送请求。"
    # 插件图标
    plugin_icon = "https://p.aiu.pub/s/5cL4Wz03.webp"
    # 插件版本
    plugin_version = "1.5.2"
    # 插件作者
    plugin_author = "wind"
    # 作者主页
    author_url = "https://github.com/windExplorer"
    # 插件配置项ID前缀
    plugin_config_prefix = "gotify_"
    # 加载顺序
    plugin_order = 14
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _webhook_url = None
    _method = None
    _enabled = False

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._webhook_url = config.get("webhook_url")
            self._method = config.get('request_method')

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        request_options = ["POST", "GET"]
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'request_method',
                                            'label': '请求方式',
                                            'items': request_options
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 8
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'webhook_url',
                                            'label': 'webhook地址'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                ]
            }
        ], {
            "enabled": False,
            "request_method": "POST",
            "webhook_url": ""
        }

    def get_page(self) -> List[dict]:
        pass

    @eventmanager.register(EventType)
    def send(self, event):
        """
        向第三方Webhook发送请求
        """
        if not self._enabled or not self._webhook_url:
            return

        def __to_dict(_event):
            """
            递归将对象转换为字典
            """
            if isinstance(_event, dict):
                for k, v in _event.items():
                    _event[k] = __to_dict(v)
                return _event
            elif isinstance(_event, list):
                for i in range(len(_event)):
                    _event[i] = __to_dict(_event[i])
                return _event
            elif isinstance(_event, tuple):
                return tuple(__to_dict(list(_event)))
            elif isinstance(_event, set):
                return set(__to_dict(list(_event)))
            elif hasattr(_event, 'to_dict'):
                return __to_dict(_event.to_dict())
            elif hasattr(_event, '__dict__'):
                return __to_dict(_event.__dict__)
            elif isinstance(_event, (int, float, str, bool, type(None))):
                return _event
            else:
                return str(_event)

        dict_data = __to_dict(event.event_data)
        data_title = dict_data.get('title', '-')
        data_message = dict_data.get('text', data_title)
        event_info = {
            "title": "MoviePilot" + data_title,
            "message": data_message,
        }

        if data_message == '-':
            logger.info("发送失败：没有获取到消息内容"  )
            logger.info("消息记录：%s" % str(dict_data))
            logger.info("data消息记录：%s" % str(event.event_data))
        else:
            if self._method == 'POST':
                ret = RequestUtils(content_type="application/json").post_res(self._webhook_url, json=event_info)
            else:
                ret = RequestUtils().get_res(self._webhook_url, params=event_info)
            if ret:
                logger.info("发送成功：%s" % self._webhook_url)
                logger.info("消息记录：%s" % str(dict_data))
                logger.info("data消息记录：%s" % str(event.event_data))
            elif ret is not None:
                logger.error(f"发送失败，状态码：{ret.status_code}，返回信息：{ret.text} {ret.reason}")
            else:
                logger.error("发送失败，未获取到返回信息")

    def stop_service(self):
        """
        退出插件
        """
        pass
