// global
'use strict';
let getIdByNameButton = document.getElementById('getIdByName');
getIdByNameButton.addEventListener('click', (event) => {
    getIdByName();
});
let getResponseButton = document.getElementById('getResponse');
getResponseButton.addEventListener('click', (event) => {
    getResponse(); 
});
let input = document.getElementById('elementName');
// functions
async function sendDeleteRequest() {
    let baseUrl = window.location.href;
    let elem = document.getElementById('deleteBtn');
    let href = elem.getAttribute('href');
    let url = new URL(href, baseUrl);
    let headers = new Headers();
    headers.append('X-CSRFToken', csrf);
    let options = {
        method: 'POST',
        headers,
    }
    // получаем ответ render от контроллера delete
    // этот ответ содержит готовый html
    let response = await fetch(url, options);
    // получим html из ответа
    let text = await response.text();
    // перепишем текущий документ полученным html
    document.write(text);
    document.close();
}

function getInputValue(element) {
    return element.value;
}


async function getIdByName() {
    let baseUrl = window.location.href;
    
    let href = getIdByNameButton.getAttribute('href');
    let parts=[baseUrl].concat([href]);
    let url = joinUrl(parts)
    let val = getInputValue(input);
    let query=createQueryParamsFromInput(val);
    url = url + query;
    let headers = new Headers();
    headers.append('X-CSRFToken',csrf);
    let options = {
        method: 'GET',
        headers
    };
    let response=await fetch(url,options);
    let text = await response.text();
    document.write(text);
    document.close();
}

async function getResponse() {
    let baseUrl = window.location.href;
    let href = getResponseButton.getAttribute('href');
    let url = new URL(href, baseUrl);
    let val = getInputValue(input);
    url=getUrl(url,val);
    let options = getGetOptions();
    let response = await fetch(url, options);
    let text = await response.text();
    document.write(text);
    document.close();
    
}

function getGetOptions() {
    let headers = new Headers();
    headers.append('X-CSRFToken',csrf);
    let options = {
        method: 'GET',
        headers
    };
    return options;
}

function getUrl(base,s) {
    let params = createPathParamsFromInput(s);
    let array = [base].concat(params);
    let url = joinUrl(array);
    return url;
}

function createPathParamsFromInput(s) {
    let pattern = /[\/;:, ]/gm;
    s=s.replace(pattern,'/');
    let list = s.split('/');
    let url=joinUrl(list);
    return url;
}


function createQueryParamsFromInput(s) {
    let pattern = /[\/;:, ]/gm;
    let list = s.split(pattern);
    let dict = {
        'collection': list[0],
        'name': list[1]
    };
    let key1 = Object.keys(dict)[0];
    let key2 = Object.keys(dict)[1];
    let query = `?${key1}=${dict.collection}&${key2}=${dict.name}`;
    return query;
}

function joinUrl(array) {
    let pattern1=/(?<!:\/)(?<!:)\/+/gm;
    let pattern2=/\/+$/gm;
    let url = array.join('/');
    url = url.replace(pattern1, '/');
    url=url.replace(pattern2,'');
    return url;
}

function addUrlParams(url,params) {
    
    return url
}

function getIntRand() {
    let rand = 0;
    rand = Math.random() * 0xFFFFFF;
    rand=Math.ceil(rand);
    return rand;
}

function setCookie(rand) {
    document.cookie=`id${rand}=${rand}`;
}
function deleteCookie(id) {
    let name=`id${id}`;
    setCookie(name, "", {
      'max-age': -1
    })
}
function getCookie(id) {
    let name=`id${id}`;
    let matches = document.cookie.match(new RegExp(
      "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
    ));
    return matches ? decodeURIComponent(matches[1]) : undefined;
  }



