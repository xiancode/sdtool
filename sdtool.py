#!/usr/bin/env  python
#-*-coding=utf-8-*-
#author shizhongxian@126.com

import sys
import os
import urllib
import string
import errno
import shutil
import codecs

content_type = sys.getfilesystemencoding()

def table2rec(table_file_name,rec_file_name=None):
    '''
    table文件转化为rec，第一行为字段名
    '''
    sufix = os.path.splitext(table_file_name)[1]
    pos = table_file_name.find(sufix)
    if not rec_file_name:
        rec_file_name = table_file_name[:pos]+"_REC"+sufix
    fout = open(rec_file_name,"w")
    
    fin = open(table_file_name)
    line = fin.readline()
    fields_str = line.strip()
    fields = fields_str.split("\t")
    fields_num = len(fields)
    line_no = 0
    #从第二行开始
    line = fin.readline()
    while line:
        line_no += 1
        if line_no % 5000 == 0:
            print "processing:",line_no,"lines"
        rec_items = []
        #line = fin.readline()
        #record = line.strip()
        items = line.split("\t")
        if len(items) == fields_num:
            rec_items.append("<REC>")
            for i  in range(fields_num):
                rec_items.append("<"+fields[i]+">="+items[i])
            fout.write("\n".join(rec_items))
            #print line
            #fout.write("\n")
        else:
            print line_no, line,"length:",len(items),"切分后个数不等于字段个数"
            for tmp in items:
                print tmp
        line = fin.readline()
    print "completed ",line_no,"lines"
    fout.close()

def rec2table(rec_filename,table_name,max_fields_num=100):
    '''
    rec文件转化为table，字段之间用制表符分割
    '''
    fout = open(table_name,"w")
    fin    = open(rec_filename)
    line = fin.readline()
    if line.strip() !="<REC>":
        print "REC文件内容不正确，请检查文件:".decode("utf-8").encode(content_type),rec_filename
        sys.exit()
    indicators = []
    index_num = 0
    #获取指标名称
    while line:
        line = fin.readline()
        if line.strip() !="<REC>":
            pos  = line.find(">=")
            indicator = line[1:pos]
            indicators.append(indicator)
            index_num += 1
        elif  line.strip() == "<REC>":
            break
        if index_num > max_fields_num:
            print "REC文件的字段超过了最大字段限制,请检查REC文件,或增大max_fields_num参数".decode("utf-8").encode(content_type)
            break;
    fin.close()
    fout.write("\t".join(indicators)+"\n")
    #
    print "当前REC文件中指标为:".decode("utf-8").encode(content_type)
    for indicator in indicators:
        print indicator
    # 转化为table
    line_no  = 0
    fin    = open(rec_filename)
    line = fin.readline()
    values = []
    records = 0
    while line:
        line = fin.readline()
        line_no += 1
        if line_no % 5000 == 0:
            print "transform ",line_no,"line"
        if line.strip() != "<REC>":
            pos = line.find(">=")
            if pos == -1:
                continue
            value = line[pos+2:]
            value = value.strip()
            values.append(value) 
        if line.strip() == "<REC>":
            #判断列表长度是否等于指标数
            if len(values) == index_num:
                #输出值
                fout.write("\t".join(values)+"\n")
                records += 1
            values = []
    #输出最后一条记录
    if len(values) == index_num:
                #输出值
                fout.write("\t".join(values)+"\n")
                records += 1
    fout.close()
    print "转化".decode("utf-8").encode(content_type),records,"条记录".decode("utf-8").encode(content_type)
    return table_name

def save_page(url,fname,save_dir):
    '''
    保存网页
    '''
    try:
        page = urllib.urlopen(url)
        data = page.read()
        outfile_name = os.path.join(save_dir,fname)
        fout = open(outfile_name,"w")
        fout.write(data)
        fout.close()
        return data
    except Exception,e:
        print url,fname,e

def load_list(fname,header=False):
    '''
    载入列表,每行为列表的一个元素
    header : 第一行是否为标题
    '''
    count = 0
    result = []
    with open(fname) as f:
        lines = f.readlines()
        for line in lines:
            count += 1
            if header and count == 1:
                continue
            result.append(line.strip())
    return result


def load_dict(tdfile,key_col,value_col_list,header=False):
    """
    根据文件和列来构造dict数据结构
    :params tdfile: 纯文本 表格样式的文件,列之间用"\t"分割 
    :params key_col:key列号,从0开始
    :params value_col_lilst:充当value的列号，列表形式[1,2,4],列号必须递增 
    """
    result = {}
    fin = open(tdfile)
    if header:
        line = fin.readline()
    line_no = 0
    line = fin.readline()
    if len(line.split("\t"))-1 < value_col_list[-1] or len(line.split("\t"))-1 < key_col :
        print "输入的列号大于文件列号"
        sys.exit() 
    while line:
        line_no += 1
        if line_no%500==0:
            print "加载数据 ",line_no," "
        items = line.split("\t")
        if len(items)-1 < value_col_list[-1] or len(items)-1 < key_col:
            print line," 列数小于输入的列数"
        else:
            if result.has_key(items[key_col]):
                pass
            else:
                tmp_list = []
                for i in value_col_list:
                    tmp_list.append(items[i].strip())
                result[items[key_col]] = tmp_list
        line = fin.readline()
    fin.close()
    return result

def merge(finame,col,d,foutname):
    """
    对于文件finame中的列col,
    从词典d中查找都col列值对应的值,形成新的列
    并和原文件finame合并,写入到文件foutname中
    :params filename  输入文件
    :params col  输入文件需要查找的列,从0开始
    :params d  查找词典
    :params foutname 输出文件
    
    """
    fin = open(finame)
    fout = open(foutname,"w")
    file_no = 0
    line = fin.readline()
    item_num = len(line.split("\t"))
    while line:
        #line = line.strip()
        file_no += 1
        if file_no%500 == 0:
            print "处理数据: ",file_no,"条"
        items = line.split("\t")
        
        if len(items) == item_num:
            tmp_str = ""
            if col == 0:
                pass 
            elif col >=1:
                for i in range(col):
                    tmp_str += items[i]+"\t" 
            else:
                print "输入列参数有错误"
                sys.exit()
            key = items[col]
            if d.has_key(key) :
                tmp_str += key+"\t"
                for d_item in d[key]:
                    tmp_str += d_item.strip() + "\t"
                for i in range(col+1,len(items)-1):
                    tmp_str += items[i].strip() + "\t"
                tmp_str += items[len(items)-1].strip()
                #print items[len(items)-1].strip(),"------"
                #print tmp_str,'____'
                tmp_str += "\n"
                tmp_str2 = tmp_str.strip()
                tmp_str2 = tmp_str2.strip("\t")
                if tmp_str2 != "":
                    fout.write(tmp_str)
                    #print tmp_str,"------"
                else:
                    print items[0]," 字典中没找到，或此条目字典格式不正确" 
        else:
            print line,"格式有错误"    
        line = fin.readline()
    fin.close()
    fout.close()

def del_tabs(s):
    '''
    删除字符串中的制表符和换行
    '''
    result_str = s.strip()
    result_str = string.replace(result_str, "\t", " ")
    result_str = string.replace(result_str, "\n", " ")
    return result_str

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def get_year_and_month(startyear=2011,startmonth=1,endyear=2015,endmonth=5):
    '''
    根据起始年月数字，产生年月列表
    '''
    year_month_list = []
    for i in range(startyear,endyear):
        for j in range(startmonth,13):
            year_month_list.append(str(i)+"年-"+str(j)+"月")
    for j in range(1,endmonth+1):
            year_month_list.append(str(endyear)+"年-"+str(j)+"月")
    return year_month_list

def sorteddict(d):
    '''
    按照字典中的k排序字典,返回排序后的元组列表
    '''
    return [(k,d[k]) for k in sorted(d.keys())]

def copy_and_overwrite(from_path, to_path):
    if os.path.exists(to_path):
        shutil.rmtree(to_path)
    shutil.copytree(from_path, to_path)
    
def str_q2b(ustring):
    '''
    将字符串全角转半角
    @author: Jasmine
    '''
    rstring=""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 12288:                              #全角空格直接转换            
            inside_code = 32 
        elif (inside_code >= 65281 and inside_code <= 65374): #全角字符（除空格）根据关系转化
            inside_code -= 65248

        rstring += unichr(inside_code)
    return rstring

def is_chinese(uchar):
    '''
    判断一个unicode是否是汉字
    @author: Jasmine
    '''
    if uchar>=u'\u4e00' and uchar<=u'\u9faf5':
        return True
    else:
        return False
 
def str_has_ch(ustring):
    flag=False
    for uchar in ustring:
        if is_chinese(uchar):
            flag=True
            break
    return flag    
            
       
def file_q2b(file_in):
    '''
    把整个文件全角转半角
    @author: Jasmine
    '''
    sufix = os.path.splitext(file_in)[1]
    fout_name=os.path.splitext(file_in)[0]+'_q2b'+sufix
    fout=codecs.open(fout_name,'w+','UTF-8')
    fin=open(file_in,'r') 
    lines = fin.readlines()
    for line in lines:
        line=line.decode('utf8').strip()
        line = str_q2b(line)
        fout.writelines(line+'\n')
    fin.close()    
    fout.close()   
    return fout_name

def file_merge(file_in):
    '''
    对rec文件进行多行合并，把没有‘=’的行合并到上一行
    @author: Jasmine
    '''
    sufix = os.path.splitext(file_in)[1] 
    fout_name=os.path.splitext(file_in)[0]+'_merge'+sufix
    finf_name=os.path.splitext(file_in)[0]+'_merge_info'+sufix
    #读取待处理文件test1.txt
    fin=open(file_in,'r') 
    lines = fin.readlines()
    #建立处理后文件
    fout=codecs.open(fout_name,'w+','UTF-8')
    #建立抛出文件
    finf=codecs.open(finf_name,'w+','UTF-8')
    #定义参数
#     lineTemp=u''   
#     numFlag=0
    lines2=[]
    
    for i in range(0,len(lines)):
        line=lines[i].strip()
        if line=='<REC>' or line.find('=')!=-1:
            lines2.append(line+'\n')
            continue
        else:
            lineStr= lines2[len(lines2)-1].strip()+' '+lines[i].strip()+'\n'
            lines2[len(lines2)-1]=lineStr
            finf.write('line'+str(i+1)+':'+lines[i].decode('utf8'))        
    for line in lines2:
        #去除空格
        line=line.replace(' ','')
        fout.writelines(line.decode('utf8'))
    
    fin.close()
    fout.close()
    finf.close()
    return fout_name

def get_file_from_dir(dirname):
    '''
    返回目录下的文件名
    相对路径
    '''
    file_list = []
    for root,dirs,filenames in os.walk(dirname):
        for filename in filenames:
            file_list.append(os.path.join(root,filename))
    return file_list

def U8_GBK(sourceFileName,targetFileName):
    '''
    
    '''
    BLOCKSIZE = 1048576 # or some other, desired size in bytes
    with codecs.open(sourceFileName, "r", "utf-8") as sourceFile:
        with codecs.open(targetFileName, "w", "gbk") as targetFile:
            while True:
                contents = sourceFile.read(BLOCKSIZE)
                if not contents:
                    break
                targetFile.write(contents)
                
            
def GBK_U8(sourceFileName,targetFileName):
    '''
    
    '''
    BLOCKSIZE = 1048576 # or some other, desired size in bytes
    with codecs.open(sourceFileName, "r", "gbk") as sourceFile:
        with codecs.open(targetFileName, "w", "utf-8") as targetFile:
            while True:
                contents = sourceFile.read(BLOCKSIZE)
                if not contents:
                    break
                targetFile.write(contents)
    
if __name__ == "__main__":
    #table2rec("extra_name_unit_data.dat")
    rec2table("jck.txt","jck_table.txt",max_fields_num=100)
    pass

    
