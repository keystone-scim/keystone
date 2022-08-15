import logging

from loguru import logger

_red = "\033[0;31m"
_nc = "\033[0m"

VERSION = "0.1.0-rc.1"
LOGO = f"""
                            {_red}7P555555555555555P!{_nc}
                        .^!7{_red}^55YYYYYYYYYYYYY55^{_nc}?!^.
                    .^!7??7?!{_red}7PYYYYYYYYYYYYYP!{_nc}7?77?7!^.
                .^!7??7!!!!7J{_red}^55YYYYYYYYYYY5Y{_nc}~J7!!!!7??7!^.
             ^~7??7!!!!!!!!!?7{_red}7PYYYYYYYYYYYP!{_nc}7?!!!!!!!!!7??7!^
           ~!7J?!!!!!!!!!!!!!J{_red}~55YYYYYYYYY5Y{_nc}~J!!!!!!!!!!!!!?J7!~
         :????!7?7!!!!!!!!!!~?7{_red}7PYYYYYYYYYP{_nc}!?7~!!!!!!!!!!7?7!????:
        ~J7!!7??7??7!!!!!!!!~!J{_red}~55YYYYYYY5Y{_nc}~J~~!!!!!!!!7?77??7!!7J~
      .7J7!!!!!7?77??7!!!!!~~~??{_red}!5YYYYYYY5{_nc}!??~~~!!!!!7??7??7!!!!!7J7.
     ^??!!!!!!!!!!?77??!!!!777!^...........^!777!!!!??77?!!!!!!!!!!??^
    !J7!!!!!!!!!!~~!?77??7!~:                 :^!7??77?!~!!!!!!!!!!!7J!
  :?J!!!!!!!!!!!!!~~~7J^:                         .^J7~~~!!!!!!!!!!!!!J?:
 .77777777!!!!!!!!!~7?^                             ^?7~!!!!!!!!!77777777.
 ~J777777777777!!!!?7.                               .7?!!!!777777777777J~
 7J!!!!77777777777?~                                   ~?77777777777!!!!J!
 ??!!!!!!!!!!!!77?^                                     ^?77!!!!!!!!!!!!??
.J7!!!!!!!!!!~~~!J:                                     :J!~~~!!!!!!!!!!7J.
^J7!!!!!!!!!!!!~7?              ----------              .J7!!!!!!!!!!!!!7J:
!J!!!!!!!!!!!!!!?7               KEYSTONE                ??!!!!!!!!!!!!!!J~
J??77!!~~^^::..                 ----------                  ...::^^~!!777??
"""


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
