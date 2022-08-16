import logging

from loguru import logger

_red = "\033[0;31m"
_nc = "\033[0m"

VERSION = "0.1.0-rc.3"
LOGO = """
                            ..............                            
                           .--------------. :                         
                      :=#%. -------------: -@%*=.                     
                  .=*%@@@@+ :------------. #@@@@@%+-.                 
              .-*%@@@@@@@@%. ------------ -@@@@@@@@@@#+:              
             *@@@@@@@@@@@@@+ :----------. #@@@@@@@@@@@@@%:            
          -#- -%@@@@@@@@@@@%  ---------- :@@@@@@@@@@@@%= :*#.         
         +@@@#. =%@@@@@@@@@@= :--------. *@@@@@@@@@@@+..*@@@%:        
       .#@@@@@@*..*@@@@@@@@@%  -------- .@@@@@@@@@@#: +%@@@@@@=       
      -%@@@@@@@@%+ :#@@@@@@@%-  ......  :#@@@@@@@#- =%@@@@@@@@@*.     
     +@@@@@@@@@@@@%= -#@%*=:               -+#@%= -#@@@@@@@@@@@@%:    
   .#@@@@@@@@@@@@@@@%- :                      . :#@@@@@@@@@@@@@@@@+   
   .-+*%@@@@@@@@@@@@%=                          .#@@@@@@@@@@@@%#+-:   
  =#*=:..:=*%@@@@@@%:                             =%@@@@@%*+-. :-+#%  
  *@@@@@%*=-. :=+#*                                :#*=-..:=*#@@@@@@: 
  #@@@@@@@@@@%#+-.                                   -+*%@@@@@@@@@@@= 
  @@@@@@@@@@@@@@@+                                   @@@@@@@@@@@@@@@* 
 :@@@@@@@@@@@@@@@-                                   #@@@@@@@@@@@@@@# 
 =@@@@@@@@@@@@@@@:                                   +@@@@@@@@@@@@@@@ 
 -+++++++++++++++                                    :+++++++++++++++ 
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
