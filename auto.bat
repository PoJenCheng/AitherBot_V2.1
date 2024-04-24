pyinstaller --noconfirm main.spec
xcopy FunctionLib_UI\ dist\main\_internal\FunctionLib_UI\ /y
xcopy FunctionLib_Robot\ dist\main\_internal\FunctionLib_Robot\ /y
xcopy FunctionLib_Vision\ dist\main\_internal\FunctionLib_Vision\ /y
xcopy pylltLib\ dist\main\_internal\pylltLib\ /y