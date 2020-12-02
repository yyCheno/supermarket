def check_PosIntnumber(s):#检查一个字符串是否为正数
    if check_number(s)!=True: return False
    try:
        int(s)
    except ValueError:
        return False
    return True
def check_Negnumber(s):#检查一个字符串是否为负数
    if check_number(s) != True: return False
    if int(s)>0:return False
    return True
def check_number(s):
    try:
        float(s)
    except ValueError:
        return False
    return True
s = "1.1"

print(check_number(s))
print(check_PosIntnumber(s))
print(check_Negnumber(s))