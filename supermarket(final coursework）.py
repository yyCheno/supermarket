# MATH26021-Final coursework
# Student name: ZHENTU LIU
# Student id: 10443407
# Student mail: zhentu.liu@student.manchester.ac.uk

import threading
from decimal import Decimal
import pandas as pd
import prettytable as pt
import re

total = 0 

def loadStockFromFile(filename="stock.csv"):
    """
    Return a nested dictionary in json format

        Arguments:
        
            -filename 

        disc:
        
            get all the files in the file list and convert them into a josn format dictionary
    """
    stock_data = pd.read_csv(filename, header=None, index_col=0,
                             names=["name", "price", "unit", "promotion", "group", "amount"], sep="|") 
    stock = stock_data.to_dict(orient="index")  
    # 数据预处理
    for ident in list(stock.keys()):
        commodity_dict = stock[ident]
        if commodity_dict['unit'] == 'pieces': 
            if (int(commodity_dict['amount'] * 10000) / 10000 - int(commodity_dict['amount'])) != float(0):
                del stock[ident]
                continue
            commodity_dict['amount'] = int(commodity_dict['amount'])
        if commodity_dict['unit'] == 'kg':  
            commodity_dict['amount'] = float(commodity_dict['amount'])
        for commodity_attributes in commodity_dict: 
            if commodity_dict[commodity_attributes] == 'None':
                commodity_dict[commodity_attributes] = None

    return stock

def listItems(dic):
    """
       Return a data visualization table

           Arguments:
           
               -dic 

           disc:
           
               convert the data dictionary into an exportable visual table
    """
    tb = pt.PrettyTable() 
    tb.field_names = ["Ident", "Product", "Price", "Amount"]  
    tb.align["Price"] = "r" 
    tb.align['Product'] = "l"
    tb.align["Amount"] = 'c'
    if dic == {}: return tb 
    ident_list = sorted(dic.keys())
    for ident in ident_list:
        row = []
        row.append(ident)
        row.append(dic[ident]['name'])
        row.append(str(format(dic[ident]['price'], ".2f")) + " £")  
        if dic[ident]['unit'] == "kg":
            row.append(str(format(dic[ident]['amount'], ".1f")) + " " + dic[ident]['unit'])
        if dic[ident]['unit'] == "pieces":
            row.append(str(dic[ident]['amount']) + " " + dic[ident]['unit'])
        tb.add_row(row)  
    return tb

def searchStock(stock, s):
    '''
    Return a sub-dictionary

           Arguments:

               -stock 
               -s
           
           disc:
               
               Search the results that match the keywords from the stock, do not distinguish between case and return a result dictionary
    '''
    substock = {}
    for ident in stock:
        if re.search(pattern=s, string=stock[ident]['name'], flags=re.I) != None:  # 正则匹配，大小写不敏感
            substock[ident] = stock[ident]
    return substock

def addToBasket(stock, basket, ident, amount):
    """
       Return a status message

           Arguments:
          
               -stock 
               -basket    
               -ident 
               -amount 
           disc:
           
               realize the mutual transfer of goods between warehouse and shopping basket, and ensure the atomicity of data by locking operation
    """

    def check_unit(stock, basket):
        if stock[ident]["unit"] == "pieces":
            stock[ident]['amount'] = int(stock[ident]['amount'])
            basket[ident]['amount'] = int(basket[ident]['amount'])

    lock.acquire()  
    if stock.get(ident) == None:  
        msg = "The product is not what we sell."
        lock.release()  
        return msg
    if basket.get(ident) == None:  
        basket[ident] = stock[ident].copy() 
        basket[ident]['amount'] = 0         
    if amount > 0 and stock[ident]['amount'] >= amount:
        stock[ident]['amount'] = (int(stock[ident]['amount'] * 100000) - int(amount * 100000)) / 100000
        basket[ident]['amount'] = (int(basket[ident]['amount'] * 100000) + int(amount * 100000)) / 100000
        check_unit(stock, basket)
        lock.release()
        return "Sucess"
    if amount > 0 and stock[ident]['amount'] < amount:
        stock_amount = stock[ident]['amount']
        basket[ident]['amount'] = (int(basket[ident]['amount'] * 100000) + int(
            stock[ident]['amount'] * 100000)) / 100000
        stock[ident]['amount'] = 0
        check_unit(stock, basket)
        msg = "Cannot add this many " + stock[ident]['unit'] + " to the basket, only added " + str(stock_amount) + " " + \
              stock[ident]['unit']
        lock.release()
        return msg+"\n"
    if amount < 0 and basket[ident]['amount'] >= abs(amount):
        basket[ident]['amount'] = (int(basket[ident]['amount'] * 100000) - int(abs(amount) * 100000)) / 100000
        stock[ident]['amount'] = (int(stock[ident]['amount'] * 100000) + int(abs(amount) * 100000)) / 100000
        check_unit(stock, basket)
        if (basket[ident]['amount'] == 0): del basket[ident]
        lock.release()
        return "Sucess"
    if amount < 0 and basket[ident]['amount'] < abs(amount):
        basket_amount = basket[ident]['amount']
        stock[ident]['amount'] = (int(stock[ident]['amount'] * 100000) + int(basket[ident]['amount'] * 100000)) / 100000
        check_unit(stock, basket)
        basket[ident]['amount'] = 0
        msg = "Cannot remove this many " + basket[ident]['unit'] + "  from the basket, only removed " + str(
            basket_amount) + " " + \
              basket[ident]['unit']
        if (basket[ident]['amount'] == 0): del basket[ident]
        lock.release()
        return msg+"\n"

def prepareCheckout(basket):
    """
       Return None

           Arguments:
           
               -basket    

           disc:
           
               add amountPayable
    """
    if basket == {}: return
    for ident in basket:
        basket[ident]["amountPayable"] = basket[ident]["amount"]

def getBill(basket):
    '''
     Return visual bill

           Arguments:
           
               -basket   

           disc:
           
               according to the information of the shopping basket, the discount is calculated to form a bill, and the visual bill table that can be output is returned
    '''
    tb = pt.PrettyTable()
    tb.field_names = ["Product", "Price", "Amount", "Payable"]
    tb.align["Product"] = "l"
    tb.align["Price"] = "r"
    tb.align["Payable"] = "r"
    global total
    free_rows = applyPromotions(basket) 
    ident_list = sorted(basket.keys())
    for ident in ident_list:
        row = []
        row.append(basket[ident]['name'])
        row.append(str(format(basket[ident]['price'], ".2f")) + " £")
        row.append(str(basket[ident]['amount']) + " " + basket[ident]['unit'])        
        price = int(basket[ident]['price'] * 100000)
        conut = int(basket[ident]['amount'] * 100000)
        result = price * conut / 10000000000
        total = (int(total* 100000) + int(Decimal(str(result)) * 100000)) / 100000 
        if len(str(result).split(".")[1]) <= 1: result = format(result,".2f")
        row.append(str(result) + " £")
        tb.add_row(row)
        if free_rows.get(ident) != None: 
            tb.add_row(free_rows[ident])
    if total==0 : total = format(total, ".2f")
    if len(str(total).split(".")[1]) <= 1: total = format(total, ".2f")
    total = str(total) + " £"
    index = str(tb).index("\n")
    length = len("TOTAL:")+len(total)
    line = index-length
    msg = "Here is your shopping bill:\n" + str(tb) + "\nTOTAL:" +" "*line + total
    return msg

def applyPromotions(basket):
    """Return products that can be exempted from reduction and their quantity are in the format of the above visual table

           Arguments:
           
               -basket    

           disc:
           
               according to the preferential information, the preferential situation of the shopping basket can be calculated, 
               and at the same time, the situation can ensure that the merchant obtains the maximum profit and returns the preferential information
    """

    rows = {} 
    group = {}  
    free = {} 
    global total

    for ident in basket:
        if basket[ident]['promotion'] == None: continue  
        if basket[ident]["group"] == None:  
            try:
                group["None"].append(ident)
            except KeyError:
                group["None"] = []
                group["None"].append(ident)
        else:
            try:
                group[basket[ident]["group"]].append(ident)  
            except KeyError:  
                group[basket[ident]["group"]] = []  
                group[basket[ident]["group"]].append(ident)

    for key in group:  
        sub_group = group[key]
        sub_group.sort(key=lambda x: basket[x]["price"])  
    for key in group:  
        sub_group = group[key]  
        if basket[sub_group[0]]['group'] == None: 
            for ident in sub_group:
                free[ident] = int(int(basket[ident]["amount"]) / 2)   
                basket[ident]["amountPayable"] = free[ident]
        else:
            total_amount = 0 
            for ident in sub_group:
                total_amount = basket[ident]['amount'] + total_amount
            to_free = int(total_amount / 4)  
            if to_free == 0: break  
            for ident in sub_group:
                amount = basket[ident]['amount']
                if amount <= to_free: 
                    free[ident] = amount  
                    to_free = to_free - amount  
                    if to_free == 0: break  
                    continue  
                else:  
                    free[ident] = to_free  
                    break  

    for ident in free:  
        row = []
        row.append("    Promotion " + basket[ident]['promotion'])
        row.append("-" + str(format(basket[ident]['price'], ".2f")) + " £")
        row.append(str(free[ident]) + " " + basket[ident]['unit'])
        price = int(basket[ident]['price'] * 100000 * -1)
        conut = int(free[ident] * 100000)
        result = price * conut / 10000000000
        total = (int(total * 100000) + int(result * 100000)) / 100000
        if len(str(result).split(".")[1]) <= 1: result = format(result, ".2f")
        row.append(str(result) + " £")
        rows[ident] = row
    return rows

def check_PosIntnumber(s):  
    if check_number(s) != True: return False
    try:
        int(s)
    except ValueError:
        return False
    if int(s) < 0: return False
    return True

def check_Negnumber(s):  
    if check_number(s) != True: return False
    if float(s) > 0: return False
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
    *** input 0：display the basket
    *** input 1：check out
    *** input a positive interge: depending on the situation and giving specific reply
    *** input a negative interge：it will be judged as illegal input
    *** input anything else: search for product in the stock with input data as key words.
    """

    stock = loadStockFromFile()
    basket = {}
    print("*" * 75)
    print("*" * 15 + " " * 10 + "WELCOME TO STEFAN EXPRESS" + " " * 10 + "*" * 15)
    print("*" * 75, "\n")

    while True:
        s = input("Input product-Ident, search string, 0 to display basket, 1 to check out: ")
        if s == "0":  
            basket_tb = listItems(basket)  
            print("Your current shopping basket:")
            print(basket_tb)
            continue
        elif s == "1":  
            prepareCheckout(basket)  
            Bill = getBill(basket)  
            print(Bill)
            print("Thank you for shopping with us!")
            return
        elif check_PosIntnumber(s) == True:  
            while (True):
                if stock.get(int(s)) == None: 
                    print("The product is not what we sell.")
                    break
                i = input("\nIf you want to back please input 'back'.\nHow many units " + stock[int(s)][
                    "unit"] + " do you want to add to your basket?: ")  
                if i == "back": break  
                if i == "0" :
                    print("Sucess")
                    break
                if check_number(i) != True:
                    print("Illegal input,need a int or float type")
                    continue
                if stock[int(s)]["unit"] == "kg":  
                    if type(eval(i)) == float: 
                        msg = addToBasket(stock, basket, int(s), float(i))
                        print(msg)
                        break
                    else:
                        print("Illegal input,need a float type")
                        continue
                if stock[int(s)]["unit"] == "pieces":  
                    if type(eval(i)) == int:
                        msg = addToBasket(stock, basket, int(s), int(i))
                        print(msg)
                        break
                    else:
                        print("Illegal input,need a int type")
                        continue
        elif check_Negnumber(s) == True:  
            print("Illegal input")
            continue
        else:  
            substock = searchStock(stock, s)
            tb = listItems(substock)
            num = 0
            if (tb == None):
                print("There were 0 search results for '" + str(s) + "':")
                continue
            for row in tb:
                num = num + 1
            print("There were " + str(num) + " search results for '" + str(s) + "':")
            print(tb)
        continue

if __name__ == '__main__':
    lock = threading.Lock()
    main()
