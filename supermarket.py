"""
# _*_ coding: utf-8 _*_
# @Time : 2020/11/30 17:31
# @Author :
# @Version：V 2.0
# @File : supermarket.py
# @desc :修复了一些问题，剔除了一些异常输入
"""
import threading
import pandas as pd
import prettytable as pt
import re

total = 0#全局变量

def loadStockFromFile(filename="stock.csv"):
    """
    Return 一个json格式嵌套字典

        Arguments:

        filename - 文件列表

        disc:
        获取文件列表所有文件，转换成一个josn格式字典
    """
    stock_data = pd.read_csv(filename,header=None,index_col=0,names=["name","price","unit","promotion","group","amount"],sep="|")#读取csv文件
    stock = stock_data.to_dict(orient="index")#转换字典
    #数据预处理
    for  ident in stock:
        commodity_dict = stock[ident]
        if commodity_dict['unit'] == 'pieces':#如果单位是pieces，数量应为整数
            commodity_dict['amount'] = int(commodity_dict['amount'])
        if commodity_dict['unit'] == 'kg':#如果单位是kg，数量应为浮点型
            commodity_dict['amount'] = float(commodity_dict['amount'])
        for commodity_attributes in commodity_dict:#处理None值
            if commodity_dict[commodity_attributes] == 'None':
                commodity_dict[commodity_attributes] = None

    return stock

def listItems(dic):
    """
       Return 一个数据化可视化表格

           Arguments:

           dic - 数据字典

           disc:
           将数据字典转换成可输出的可视化表格
    """
    if dic == {} :return None #排除空字典
    tb = pt.PrettyTable()#使用perettytable库完成可视化工作
    tb.field_names= ["Ident", " Product", "Price", "Amount"]#指定列名
    tb.align["Price"] = "r"#该列右对齐
    for ident in dic:
        row = []
        row.append(ident)
        row.append(dic[ident]['name'])
        row.append(str(format(dic[ident]['price'],".2f"))+" £")#限制保留两位小数
        row.append(str(dic[ident]['amount'])+" "+dic[ident]['unit'])
        tb.add_row(row)#将此行加入prettytable
    return tb

def searchStock(stock, s):
    '''
    Return 一个结果子字典

           Arguments:

           stock - 仓库数据字典
           s -  搜索关键字
           disc:
           从库存中模糊搜索出与关键字匹配的结果，不区分大小写
    '''
    substock = {}
    for ident in stock:
        if re.search(pattern=s,string=stock[ident]['name'],flags=re.I)!=None:#正则匹配，大小写不敏感
            substock[ident] = stock[ident]
    return substock

def addToBasket(stock, basket, ident,amount):
    """
       Return 一个状态消息

           Arguments:

           stock - 仓库数据字典
        
           basket    - 购物篮子数据字典

           ident -  商品对应ident

           amount - 处理数量
           disc:
           实现从仓库与购物篮子之间互相转移商品
    """
    lock.acquire()#加锁，保证stock数据与basket数据的原子性
    if stock.get(ident) == None:#防止用户输入不存在的商品
        msg = "The product is not what we sell."
        lock.release()#释放锁
        return msg
    if basket.get(ident) == None:#防止购物篮子不存在此商品而引发的keyerror
        basket[ident] = stock[ident].copy()#深复制
        basket[ident]['amount'] = 0#初始化，只需要数据结构而不需要数据
        #以下对应四种情况
    if amount > 0 and stock[ident]['amount'] >= amount:
        stock[ident]['amount'] = stock[ident]['amount'] - amount
        basket[ident]['amount'] = basket[ident]['amount'] + amount
        lock.release()
        return "Sucess"
    if amount > 0 and stock[ident]['amount'] < amount:
        stock_amount =  stock[ident]['amount']
        basket[ident]['amount'] = basket[ident]['amount'] + stock[ident]['amount']
        stock[ident]['amount'] = 0
        msg = "Cannot add this many "+stock[ident]['unit']+" to the basket, only added "+str(stock_amount)+" "+stock[ident]['unit']
        lock.release()
        return msg
    if amount < 0 and basket[ident]['amount'] >= abs(amount):
        basket[ident]['amount'] = basket[ident]['amount'] - abs(amount)
        stock[ident]['amount'] = stock[ident]['amount'] + abs(amount)
        if(basket[ident]['amount'] == 0): del basket[ident]
        lock.release()
        return "Sucess"
    if amount < 0 and basket[ident]['amount'] < abs(amount):
        basket_amount = basket[ident]['amount']
        stock[ident]['amount'] = stock[ident]['amount'] + basket[ident]['amount']
        basket[ident]['amount'] = 0
        msg = "Cannot remove this many " + basket[ident]['unit'] + "  from the basket, only removed " + str(basket_amount) + " " + \
              basket[ident]['unit']
        if (basket[ident]['amount'] == 0): del basket[ident]
        lock.release()
        return msg

def prepareCheckout(basket):
    """
       Return None

           Arguments:

           basket    - 购物篮子数据字典

           disc:
           添加amountPayable
    """
    for ident in basket:
        basket[ident]["amountPayable"] = basket[ident]["amount"]

def getBill(basket):
    '''
     Return 可视化账单

           Arguments:

           basket    - 购物篮子数据字典

           disc:
           根据购物篮子的信息，计算优惠后形成账单
    '''
    tb = pt.PrettyTable()
    tb.field_names = ["Product", "Price", "Amount","Payable"]
    tb.align["Product"] = "l"
    tb.align["Price"] = "r"
    tb.align["Payable"] = "r"
    global total
    free_rows = applyPromotions(basket)#获取优惠列表
    for ident in basket:
        row = []
        row.append(basket[ident]['name'])
        row.append(str(format(basket[ident]['price'],".2f"))+" £")
        row.append(str(basket[ident]['amount'])+" "+basket[ident]['unit'])
        #计算机计算浮点数要格外注意精度问题，特别是在金融系统的结算中，一般用大数封装数据进行计算
        #受Python动态语言特性影响，用大数还是出现精度问题，故通过强制转换整数方式计算
        price = int(basket[ident]['price']*100000)
        conut = int(basket[ident]['amount']*100000)
        result = price*conut/10000000000
        total = total+result#统计总金额
        row.append(str(result)+" £")
        tb.add_row(row)
        if free_rows.get(ident) != None:#如果该商品有优惠信息
            tb.add_row(free_rows[ident])
    total=str(total)+" £"
    msg = "Here is your shopping bill:\n"+str(tb)+"\nTOTAL:"+total
    return msg
def applyPromotions(basket):

    """Return 可以免减的商品及其数量，格式为上述可视化表格的格式

           Arguments:

           basket    - 购物篮子数据字典

           disc:
           根据优惠信息计算出该购物篮子的优惠情况，同时该情况可以保证商家获取的是最大利润
    """

    rows = {}#可以免减的商品及其数量字典，格式为上述可视化表格的格式
    group = {}#优惠分组
    free = {}#可以免减的商品及其数量字典，格式为{ident:amuout}
    global total

    for ident in basket:
        if basket[ident]['promotion'] == None:continue#没有优惠的直接跳过，节省程序资源
        if basket[ident]["group"] == None :#单商品优惠
            try:
                group["None"].append(ident)
            except KeyError:
                group["None"] = []
                group["None"].append(ident)
        else:
            try:
                group[basket[ident]["group"]].append(ident)#将同一组的商品放在一个列表中
            except KeyError:#防止使用字典中不存在的key时，引发的keyeeror
                group[basket[ident]["group"]] = []#先初始化一个key
                group[basket[ident]["group"]].append(ident)

    for key in group:#对于每个组，按最便宜的在前面，排序之
        sub_group = group[key]
        sub_group.sort(key=lambda x:basket[x]["price"])#按价格排序
    for key in group:#开始处理每个组的优惠信息
        sub_group = group[key]#每组商品列表
        if basket[sub_group[0]]['group'] == None:#如果是单商品，直接处理
            for ident in sub_group:
                free[ident] = int(int(basket[ident]["amount"])/2) +  int(basket[ident]["amount"])%2#满二付一
                basket[ident]["amountPayable"] = free[ident]
        else:
            get = 4
            pay = 3
            to_free = get - pay#可以减免的商品数量
            tmp_free = {}#缓冲区
            total_amount = 0#商品总量
            for ident in sub_group:
                amount = basket[ident]['amount']
                total_amount = amount+total_amount
                if amount <= to_free:#如果该商品数量不够或者刚好够
                    tmp_free[ident] = amount#减免该商品所有的数量
                    to_free = to_free -amount#更新还可以减免多少
                    continue#去寻找下一个商品
                else :#如果该商品数量够了
                    tmp_free[ident] = to_free#正常处理就行
                    break#够了不用去寻找下一商品，直接退出
            if total_amount >= get:#如果商品总量比get的大，则代表可以满减
                for tmp_ident in tmp_free:
                    free[tmp_ident] = tmp_free[tmp_ident]#将缓冲区的数据写入减免字典
                    basket[ident]["amountPayable"] = free[tmp_ident]

    for ident in free:#转换成表格格式返回
        row=[]
        row.append("    Promotion "+basket[ident]['promotion'])
        row.append("-"+str(format(basket[ident]['price'], ".2f")) + " £")
        row.append(str(free[ident]) + " " +basket[ident]['unit'] )
        price = int(basket[ident]['price'] * 100000*-1)
        conut = int(free[ident] * 100000)
        result = price * conut / 10000000000
        total = total + result
        row.append(str(result) + " £")
        rows[ident] = row
    return rows

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
# Task 7
def main():
    """
    TODO: include a docstring
    """

    stock = loadStockFromFile()
    basket = {}
    print("*"*75)
    print("*"*15+" "*10+"WELCOME TO STEFAN EXPRESS"+" "*10+"*"*15)
    print("*"*75,"\n")

    while True:
        s = input("Input product-Ident, search string, 0 to display basket, 1 to check out: ")
        if s == "0":#看购物篮子
            basket_tb = listItems(basket)#获取购物篮子
            if basket_tb != None:
                print("Your current shopping basket:")
                print(basket_tb)
                continue
            else:#空篮子
                print("Your shopping basket is empty!")
                continue
        elif s == "1" :#结账
            if basket =={}:
                print("Your shopping basket is empty!")
                continue
            prepareCheckout(basket)#预结账
            Bill = getBill(basket)#获取账单
            print(Bill)
            print("Thank you for shopping with us!")
            continue
        elif check_PosIntnumber(s) ==True :#如果识别为正整数，则应该是商品ident
            while(True):
                if stock.get(int(s)) == None:#没有这个商品
                    print("The product is not what we sell.")
                    break
                i = input("How many units "+stock[int(s)]["unit"]+" do you want to add to your basket? \nIf you want to back please input 'back': ")#有的话则询问下一步
                if i == "back" :break#用户退出二级菜单
                if check_number(i) != True:
                    print("Illegal input,need a int or float type")
                    continue
                if stock[int(s)]["unit"] =="kg":#kg单位
                    if type(eval(i)) == float:#检查当单位是kg是，是不是浮点型
                        msg = addToBasket(stock,basket,int(s),float(i))
                        print(msg)
                        break
                    else:
                        print("Illegal input,need a float type")
                        continue
                if stock[int(s)]["unit"] == "pieces":#---
                    if type(eval(i)) == int:
                        msg = addToBasket(stock,basket,int(s),int(i))
                        print(msg)
                        break
                    else:
                        print("Illegal input,need a int type")
                        continue
        elif check_Negnumber(s) == True:#暂时未对负数定义何种功能
            print("Illegal input")
            continue
        else:#其他情况属于字符串类型，视为搜索商品
            substock = searchStock(stock,s)
            tb = listItems(substock)
            num = 0
            if(tb == None):
                print("There were 0 search results for '"+str(s)+"':")
                continue
            for row in tb:
                num = num + 1
            print("There were "+str(num)+" search results for '"+str(s)+"':")
            print(tb)

        continue




if __name__ == '__main__':
    lock = threading.Lock()
    main()




