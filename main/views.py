from hashlib import new
from importlib.resources import path
from os import listdir, remove
from pathlib import Path
from tkinter.messagebox import NO
from django.shortcuts import redirect
from django.shortcuts import render
import random
from urllib.parse import urljoin
from requests.models import Response
import requests
import json
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from varname import nameof
from main.selenium import runSeleniumTest
import re
from django.views import View
from urllib import parse
requests.packages.urllib3.disable_warnings()


class ResponseRestApiTestLine:
    def __init__(self, id, url, method, statusCode, response, content=None, color=None, reason=None):
        self.id = id
        self.url = url
        self.statusCode = statusCode
        if reason != None:
            self.reason = reason
        self.content = content
        self.color = color
        self.method = method
        self.response = response

def restApi(request):
    if request.method == 'POST':
        data = runRestApiTest(request)
        return render(request,'index.html',data)
    else:
        return render(request,'index.html')


def html(request):
    if request.method == 'POST':
        data = runHtmlApiTest(request)
        return render(request, 'index.html', data)
    else:
        return render(request, "index.html")
    
def delete(request):
    data=deletePutRequestsResults(request)
    lines=data['file']
    codes=[x.statusCode for x in lines]
    
    if 400 not in codes and 500 not in codes:
        deleteCookies(request)
        ClearCache()
    return render(request,'index.html',data)


file=str()
def runRestApiTest(request):

    js = str()
    lines = list()
    p=''
    filename=''
    global file
    
    try:
        # если файл загружен
        file=request.FILES['file']
        p='uploads'
        filename=file.name
    except:
        # если файл не загружен, использовать локальный файл для примера
        p='design'
        filename='yandex-rasp-test.yml'
        # return render(request, "index.html")
    parts=[p,filename]
    path=joinUrl(parts)
    if file!='':
        HandleUploadedFile(file,path, request)
    js = "alert('Файл загружен')"
    yamlDict = getYamlDict(f'{path}')
    fileUploadId=getIntRand()
    setCookie(request,fileUploadId)
    lines = ProcessUrls(yamlDict,fileUploadId)
    print(f'=== {nameof(lines)}:{lines}')
    CreateDeletingFile(lines,fileUploadId)
    data = {"js": js, "file": lines}
    return data


def runHtmlApiTest(request):
    try:
        file = request.FILES['file']
    except:
        return render(request, "index.html")
    HandleUploadedFile(file, request)
    yamlDict=getYamlDict(f'uploads/{file.name}')
    list = runSeleniumTest(yamlDict)
    if len(list) == 0:
        list = {'result': 'success'}
    data = {
        'htmlTestResult': list
    }
    return data


def ProcessUrls(yamlDict,fileUploadId):

    response = Response()
    lines = []
    i = 0
    s = requests.Session()
    # получить токен
    token = GetToken(yamlDict, s)
    if token!=None:
        s.headers = {'X-Auth-Token': token}
    baseUrl = ''
    try:
        baseUrl = yamlDict['base url']
    except:
        baseUrl = ''
    urls = yamlDict['urls']
    requiredItems=list()
    for u in urls:
        url = baseUrl+u['url']
        method = u['method']
        details = ''
        try:
            details = u['details']
        except:
            details = None
        if method == 'get':
            response = s.get(url, verify=False)
            lines = AppendLine(lines, url, response, i)
            i += 1
            # методы details вызываются для каждого экземпляра, то есть сначала нужно получить id объектов
            if details != None:
                if type(details)==str:
                    dUrl = url+details
                    response = s.get(dUrl, verify=False)
                    lines = AppendLine(lines, dUrl, response, i)
                    i += 1
                    continue
                elif type(details)==list:
                    for x in details:
                        dUrl = url+x
                        response = s.get(dUrl, verify=False)
                        lines = AppendLine(lines, dUrl, response, i)
                        i += 1
                        continue
        elif method == 'post':
            body = json.dumps(u['body'])
            response = s.post(url, body, verify=False)
            lines = AppendLine(lines, url, response, i)
            i += 1
        elif method == 'put':
            # предполагается, что если уже создаваемые элементы требуют связи с другими элементами (например для servicespools требуются provider, provider/[id]/service и osmanager), то используются только те элементы, которые создаются в текущем тесте
            
            modified_body=fillIdsInBody(u['body'],requiredItems)
            body = json.dumps(modified_body)
            response = s.put(url, body, verify=False)
            lines = AppendLine(lines, url, response, i)
            i += 1
            # получить id созданного объекта для дальнейшего создания объектов details
            ids = GetIds(response)
            if len(ids) != 0:
                for id in ids:
                    ur=url+f'/{id}'
                    new_ur=re.sub('\/$','',ur)
                    new_ur = re.sub('(?<=[^:])\/\/', "/", new_ur)
                    t=getRequestUrlByItemName(new_ur)
                    if t!=None: requiredItems.append(t)
                    if details != None:
                        # предполагается, что для методов PUT details всегда будут указаны в верном формате (в форме списка объектов)
                        for x in details:
                            dUrl = url+id+x['url']
                            modified_body=fillIdsInBody(x['body'],requiredItems)
                            body=json.dumps(modified_body)
                            response = s.put(dUrl, body, verify=False)
                            lines = AppendLine(lines, dUrl, response, i)
                            ids_list=GetIds(response)
                            for x in ids_list:
                                ur=dUrl+f'/{x}'
                                new_ur=re.sub('\/$','',ur)
                                new_ur = re.sub('(?<=[^:])\/\/', "/", new_ur)
                                t=getRequestUrlByItemName(new_ur)
                                if t!=None: requiredItems.append(t)
                            i += 1
                            continue
            
        elif method == 'delete':
            response = s.delete(url, verify=False)
            lines = AppendLine(lines, url, response, i)
            i += 1
    # CreateDeletingFile(lines,fileUploadId)
    
    return lines


def HandleUploadedFile(f,path, request):
    with open(f'{path}', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def GetToken(yamlDict, s):
    baseUrl = yamlDict['base url']
    urls = yamlDict['urls']
    try:
        authentication = json.dumps(yamlDict['authentication'])
    except:
        return None
    # проверить, существует ли в urls строка с частью login
    loginExists = False
    loginUrl = baseUrl
    for url in urls:
        if 'login' in url['url']:
            loginExists = True
            loginUrl = baseUrl+url['url']
            break
    if loginExists == False:
        # raise Exception("=== путь для аутентификации не найден в файле")
        return None
    response = s.post(loginUrl, authentication, verify=False)
    token = json.loads(response.text)
    try:
        token = token['token']
    except:
        pass
    if token == None:
        # raise Exception("=== ошибка аутентификации, вероятно указаны неверные логин/пароль")
        pass
    return token


def AppendLine(lines, url, response, i):
    sc = response.status_code
    content = str()
    color = str()
    reason = response.reason
    method = response.request.method
    content = getJsonTextOrTextContent(response)
    color=getColor(sc)
    if sc==404 or ('list index out of range' in content):
        sc=404
        reason='Элемент не существует'
        color='#FF6B00'

    line = ResponseRestApiTestLine(
        i, url, method, sc, response, content, color, reason)
    lines.append(line)

    return lines

def getColor(sc):
    if sc == 200:
        color = "green"
    else:
        color = "red"
    return color

def getJsonTextOrTextContent(response):
    if 'json' in response.headers['content-type']:
        # привести к словарю
        a = json.loads(response.text)
        content = json.dumps(a, indent=4,ensure_ascii=0)
    else:
        content = response.text
    return content

def getJsonDictOrTextContent(response):
    content=str()
    if 'json' in response.headers['content-type']:
        # привести к словарю
        content = json.loads(response.text)
    else:
        content = response.text
    return content


def CreateDeletingFile(lines,fileUploadId):
    global file
    if file=='': return
    lines.reverse()
    urls=[x.url for x in lines]
    
    # создать файл для удаления элементов
    filename=f'toDelete{fileUploadId}.yml'
    f = open(f'uploads/{filename}', 'w')
    # отступы ВАЖНЫ!
    str = '''
authentication:
  auth: DB
  username: admin
  password: optical-bells1
base url: ''
urls:
  - url: https://10.1.140.106/uds/rest/auth/login/
    details:
    method: post
    body: 
      auth: DB
      username: admin
      password: optical-bells1

    '''
    f.write(str)
    f.close()
    for x in lines:
        id = GetIds(x.response) 
        if len(id) != 0:
            id = id[0]
            id = id.replace("'", '')
            id = id.replace("/", '')
        else:
            id = ''
        f = open(f'uploads/{filename}', 'a')
        u = x.url+"/"+id
        u = re.sub('(?<=[^:])\/\/', "/", u)
        u=re.sub('\/$','',u)
        if 'login' not in u:
            f.write(f'\n  - url: {u}')
            f.write(f'\n    method: delete')
    f.close()


def GetIds(response):

    lstIds = []
    if 'json' in response.headers['content-type']:
        a = json.loads(response.text)
        if type(a)==list and len(a) != 0:
            for x in a:
                if 'id' in x:
                    id = x['id']+"/"
                    lstIds.append(id)
        elif type(a)==dict:
            if 'id' in a:
                id = a['id']+"/"
                lstIds.append(id)
    return lstIds


def CheckPutObjectExistance(response):

    pass


class DeleteItems(View):
    def post(self,request):
        js = str()
        yamlDict=getYamlDict('uploads/toDelete.yml')
        lines = ProcessUrls(yamlDict)
        data = {"js": js, "file": lines}
        return render(request,'index.html',data)
    def get(self,request):
        js = str()
        yamlDict=getYamlDict('uploads/toDelete.yml')
        lines = ProcessUrls(yamlDict)
        data = {"js": js, "file": lines}
        
        return render(request,'index.html',data)
    
def deletePutRequestsResults(request):
    cookies=getCookies(request)
    keys=cookies.keys()
    items=cookies.items()
    js = str()
    lines=list()
    for id in items:
        id=id[1]
        filename=f'toDelete{id}.yml'
        path=f'uploads/{filename}'
        file=Path(path)
        
        if file.is_file()==False: continue
        yamlDict=getYamlDict(f'uploads/{filename}')
        # в lines результат всех запросов, чтобы отобразить что было удалено, получается для каждого id будет свой список
        thisBlockLines=ProcessUrls(yamlDict,id)
        for x in thisBlockLines:
            lines.append(x)
    data = {"js": js, "file": lines}
    return data


def getIntRand(): 
    rand=random.randint(1,1000000)
    return rand


def setCookie(request,rand): 
    id=f'id{rand}'
    request.session[f'{id}']=f'{rand}'

def deleteCookie(request,id):
    request.session.pop(id)
    
def deleteCookies(request):
    request.session.flush()

def getCookies(request):
    cookies=request.session
    return cookies
def ClearCache():
    dirPath='uploads/'
    files=listdir(dirPath)
    delFiles=[x for x in files if 'toDelete' in x]
    for x in delFiles:
        filePath=urljoin(dirPath,x)
        file=Path(filePath)
        if file.is_file()==False: continue
        try:
            remove(filePath)
        except:
            continue
    idFiles=[x for x in files if 'id' in x]
    for x in idFiles:
        filePath=urljoin(dirPath,x)
        file=Path(filePath)
        if file.is_file()==False: continue
        try:
            remove(filePath)
        except:
            continue
    
        
def getIdByNameFromRequest(request):
    yamlDict=getYamlDict('uploads/hostvm-vdi-put-tests.yml')
    session=requests.Session()
    token=GetToken(yamlDict,session)
    session.headers = {'X-Auth-Token': token}
    x=getParamsDictFromRequest(request)
    baseUrl='https://10.1.140.106/uds/rest'
    urlParts=[baseUrl,x['collection']]
    name=x['name']
    
    url=joinUrl(urlParts)
    response=session.get(url,verify=False)
    content=getJsonDictOrTextContent(response)
    id=str()
    if type(content)==list:
        for x in content:
            if 'name' in x.keys():
                if name in x['name']:
                    if 'id' in x.keys():
                        id=x['id']
    elif type(content)==dict:
        pass
    else:
        pass
    
    lines=list()
    lines=AppendLine(lines,response.url,response,0)
    data={'file':lines}
    return render(request,'index.html',data)

def getIdByName(yamlDict,relPath,name):
    # аутентификация
    session=requests.Session()
    token=GetToken(yamlDict,session)
    session.headers = {'X-Auth-Token': token}
    # 
    baseUrl=yamlDict['base url']
    urlParts=[baseUrl,relPath]
    url=joinUrl(urlParts)
    response=session.get(url,verify=False)
    content=getJsonDictOrTextContent(response)
    id=str()
    if type(content)==list:
        for x in content:
            if 'name' in x.keys():
                if name in x['name']:
                    if 'id' in x.keys():
                        id=x['id']
    elif type(content)==dict:
        pass
    else:
        pass
    return id


def getResponse(request):
    # убрать части, принадлежащие url и оставить параметры, переданные из js
    yamlDict=getYamlDict('uploads/hostvm-vdi-put-tests.yml')
    params=getParamsListFromRequest(request)
    session=getAuthenticatedSession(yamlDict)
    baseUrl=getBaseUrl(yamlDict)
    parts=[baseUrl]+params
    url=joinUrl(parts)
    response=session.get(url,verify=0)
    lines=list()
    color=getColor(response.status_code)
    lines=AppendLine(lines,url,response,0)
    data={'file':lines}
    return render(request,'index.html',data)

    

def getAuthenticatedSession(yamlDict):
    session=requests.Session()
    token=GetToken(yamlDict,session)
    session.headers={'X-Auth-Token':token}
    return session

def getBaseUrl(yamlDict):
    baseUrl=yamlDict['base url']
    return baseUrl

def getUrlParts(path):
    pattern='[\/\-;:, ]'
    path=re.sub(pattern,'/',path)
    parts=path.split('/')
    return parts


def getDictFromTuples(tuples):
    d=dict()
    for x in tuples:
        d[x[0]]=x[1]
    return d

def getParamsDictFromRequest(request):
    d=dict()
    for x in request.GET:
        d[x]=request.GET[x]
    return d

def getParamsListFromRequest(request):
    parts=request.path.split('/')
    parts.pop(0)
    parts.pop(0)
    return parts

def joinUrl(parts):
    url='/'.join(parts)
    url=re.sub('(?<!:\/)(?<!:)\/+','/',url)
    url=re.sub('\/+$','',url)
    return url




def getYamlDict(path):
    file=open(path)
    content=file.read()
    print(f'=== {nameof(path)}:{path}')
    print(f'=== {nameof(file)}:{file}')
    print(f'=== {nameof(content)}:{content}')
    yamlDict=load(content,Loader=Loader)
    return yamlDict

def getRequestUrlByItemName(path):
    # TODO: имя файла должно быть произвольным, изменить!
    global file
    yaml = getYamlDict(f'uploads/{file.name}')
    baseUrl = yaml['base url']
    
    requests_naming = {
        "service_id": '.*providers\/.*(?!=services)\/.*$',
        "provider_id": '.*providers\/[^\/]*$',
        "osmanager_id": '.*\/osmanagers\/.*$',
        "transport_id": '.*\/transports\/.*$',
        "group_id": '.*\/groups\/.*$'
    }
    dct = dict()
    t = tuple()
    for (k, v) in requests_naming.items():
        if compare(v, path):
            p = path.replace(baseUrl, '')
            splits = p.split('/')
            id = splits[len(splits)-1]
            t = (k, id)

    if not t:
        return None
    else:
        return t
    
def removeBaseUrl(path,baseUrl):
    pattern=f'{baseUrl}'
    path=re.sub(pattern,'',path)
    return path
        
def compare(pattern,path):
    match=re.match(pattern,path)
    if match!=None: return True
    else: return False
        
def checkAlias(key):
    itemsRequiredIdSearch=[
        "service_id",
        "provider_id",
        "osmanager_id",
        "transport_id",
        "group_id"
    ]
    if key in itemsRequiredIdSearch: return True
    else: return False

        
def fillIdsInBody(body,requiredItems):
    print(f'=== {nameof(requiredItems)}:{requiredItems}')
    name=str()
    modified_body=dict()
    for (key,value) in body.items():
        if checkAlias(key)==True:
            if key=='transport_id' or key=='group_id': # элементы, для которых id нужно указывать без префикса, просто как 'id'
                modified_body['id']=[x[1] for x in requiredItems if x[0]==key][0]                
            else:
                modified_body[key]=[x[1] for x in requiredItems if x[0]==key][0]
        else:
            modified_body[key]=value
    return modified_body

