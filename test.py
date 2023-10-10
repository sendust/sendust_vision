import datetime
def get_timestamp(s):
    if s not in ["log", "file"]:
        s = "log"
    tm_stamp = {}
    tm_stamp["log"] = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f")
    tm_stamp["file"] = datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Mm%Ss.%f")
    return tm_stamp[s]


print(get_timestamp("1"))

