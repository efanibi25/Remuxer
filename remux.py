#!/usr/bin/env python3.8

from argparse import ArgumentParser
from os.path import basename
from subprocess import run, PIPE,STDOUT,Popen
import os
import tempfile
import json
from sh import fd,wine,winepath,sudo,bdinfo,mkvmerge,bdsup2sub
from simple_term_menu import TerminalMenu
import re
from pymediainfo import MediaInfo
from guessit import guessit
import shutil
import langcodes
from langcodes import *
from pymediainfo import MediaInfo
import argparse
import sys
from prompt_toolkit import prompt as input
from prompt_toolkit.completion import WordCompleter
import humanize
from random import randint
from collections import OrderedDict
import xmltodict
import imdb
ia = imdb.IMDb()
from nested_lookup import nested_lookup

from tmdbv3api import TMDb,Movie,TV
movie=Movie()
tv=TV()
tmdb = TMDb()
tmdb.api_key = 'f400773075f3800bb1c601f7f81f4b5e'
def main():
    parser = argparse.ArgumentParser()
    parser = parser.add_argument('path')
    parser = parser.add_argument('outpath')
    parser = parser.add_argument('-a','--api')
    mux = parser.add_mutually_exclusive_group()
    mux.add_argument('-d', '--demux', action='store_true')
    mux.add_argument('-r', '--remux', action='store_true')
    parser.add_argument('-sl','--sublanguage', nargs='+')
    parser.add_argument('-al','--audiolanguage', nargs='+')
    mux.add_argument('-s','--setorder', action='store_true')
    parser.add_argument('-u','--useorder', action='store_true')
    args=parser.parse_args()

    

    tmdb.api_key = args.api
    uid=1000
    gid=1000
    # os.chown(path, uid, gid)
    if args.demux:
        inpath=args.path
        os.chdir(inpath)
        t=fd('STREAM',inpath, '-t',"d",_tty_out=False)
        t=t.splitlines()
        menu = TerminalMenu(t)
        sources=[]
        extractdict={}
        addsource="yes"
        title=""
        while addsource=="yes" or addsource=="y" or addsource=="Y" or addsource=="YES":
            menu_index = menu.show()
            dir=t[menu_index]
            sources.append(dir)
            addsource=input("Add Another Sources for this Release?:")


        if len(sources)==0:
            print("No Sources Picked")
            input("keepgoing?:")
        sources=list(dict.fromkeys(sources))
        basefolder=os.path.basename(re.sub("/BDMV/STREAM","",sources[0]))
        basefolder=re.sub(" ",".",basefolder)

        folder=f"Mux.{os.urandom(7).hex()}.{basefolder}"
        temp=os.path.join(inpath,folder)
        os.mkdir(temp)
        os.chdir(temp)
        os.mkdir("Eac3to")
        os.mkdir("Bdinfo")







        for i in range(0,len(sources)):
            show=os.path.basename(re.sub("/BDMV/STREAM","",sources[i]))
            show=re.sub(" ",".",show)
            os.mkdir(show)
            os.chdir(show)

            element=sources[i]
            print("\n",element,"\n")
            blu=re.sub("/BDMV/STREAM","/BDMV",element)
            data,index=get_bluinfo(blu,args,i)
            data=demux(blu,data,show,index)
            if data==False:
                os.chdir("..")
                shutil.rmtree(show)
                continue


            if i==0:
                title=createTitle(data,show)
                extractdict["movietitle"]=title
                extractdict["chaptersdir"]=show
                extractdict["videodir"]=show
            extractdict[show]=data

            shutil.move(f"{show}.Eac3to.txt","../Eac3to")
            shutil.move("BDINFO.bd.txt",f"../Bdinfo/{show}.bdinfo.txt")
            cleanup(extractdict[show])


            os.chdir("..")
        if len(list(extractdict.keys()))==1:
            print("No files Demux")
            os.chdir("..")
            shutill.remove(temp)
            quit()
        # set_order(extractdict)
        print("\n",extractdict)
        fp=open("options.json","w")
        json.dump(extractdict,fp,indent=4)
        fp.close()
        export_xml(title)
        quit()
    if args.remux:
        inpath=args.path
        outpath=args.outpath
        os.chdir(inpath)
        t=fd('Mux',inpath, '-t',"d",_tty_out=False)
        t=t.splitlines()
        menu = TerminalMenu(t)
        menu_index = menu.show()
        os.chdir(t[menu_index])
        if args.useorder:
            title=remuxorder()
        else:
            title=remux()

        if os.path.isfile(os.path.join(outpath,f"{title}.mkv"))
            Delete=input("Destination File Exist Delete? ")
            if Delete=="y" or Delete=="Y" or Delete=="yes" or Delete=="Yes":
                os.remove(os.path.join(outpath,f"{title}.mkv"))
            else:
                quit()
        printInfo(f"{title}.mkv")
        shutil.move(f"./{title}.mkv",outpath)
    if args.setorder:
        os.chdir(inpath)
        t=fd('Mux',inpath, '-t',"d",_tty_out=False)
        t=t.splitlines()
        menu = TerminalMenu(t)
        menu_index = menu.show()
        os.chdir(t[menu_index])
        set_order()


def set_order():
    i =0
    sublist=[]
    audiolist=[]
    f=open('options.json',"r")
    extractdict= json.load(f)
    f.close()
    for key in extractdict:
        if key=="randomfolder" or key=="movietitle" or key=="chaptersdir" or key=="videodir" or key=="suborder" or key=="audiorder":
            continue
        for mediakey in extractdict[key]:
            if mediakey=="chapters":
                continue
            mediadict=extractdict[key][mediakey]
            title=mediadict.get("title","")
            filename=mediadict.get("file","")
            usefile=mediadict.get("useFile","No Comment")
            lang=mediadict.get("lang","No Comment")
            comment=mediadict.get("comment","No Comment")
            if re.search("Audio: ",title)!=None and usefile=="True":
                audiolist.append(f"{mediakey}:{key}:{filename}:{lang}:Comment->{comment}")
            if re.search("Subtitle: ",title)!=None and usefile=="True":
                sublist.append(f"{mediakey}:{key}:{filename}:{lang}:Comment->{comment}")
    tempdict={"audiorder":audiolist,"suborder":sublist}
    extractdict.update(tempdict)
    print(tempdict)
    update=input("Replace Current File Order?: ")
    if update=="y" or update=="Y" or update=="Yes" or update=="yes" or update=="YES":
        fp=open("options.json","w")
        json.dump(extractdict,fp,indent=4)
        fp.close()








def get_bluinfo(blu,args,sourcedex):

    t=run(["sudo","bdinfo","-l",blu,"."],stdout=PIPE)
    print(t.stdout.decode('utf8', 'strict'))
    index=input("Enter a playlist: ")
    l=t.stdout.decode('utf8', 'strict').splitlines()
    line=l[2+int(index)]
    match=re.search("[0-9][0-9][0-9][0-9][0-9].MPLS",line)
    playlist=line[match.start():match.end()]
    t=run(["sudo","bdinfo","-m",playlist,blu,"."])
    data = open('BDINFO.bd.txt', 'r')
    audiolang=args.audiolanguage
    sublang=args.sublanguage
    mediadict={}
    mediadict["chapters"]="1:chapters.txt"
    defaultset="False"


    lines = data.readlines()
    dexquick=lines.index("QUICK SUMMARY:\n")
    lines=lines[dexquick:len(lines)-1]
    for i in range(len(lines)):
        if re.search("Video: ",lines[i])!=None:
            lines=lines[i:len(lines)]
            break






    for i in range(0,len(lines)):
        currline=lines[i].rstrip()
        tempdict={}
        tempdict2={}
        key=randint(100000, 999999)
        if re.search("Video",currline)!=None:
            tempdict["title"]=currline
            mediadict["video"]=tempdict
            continue
        lang=re.sub("Audio: |Video: |Subtitle: ","",currline).split("/")[0]
        lang=re.sub(" $","",lang)
        lang=re.sub("^ ","",lang)
        lang=re.sub("\* ","",lang)
        code=langcodes.find(lang)
        code=  standardize_tag(code)
        title=re.sub(f"{lang} /","",currline)
        title=re.sub("\(","",title)
        title=re.sub("\)","",title)
        title=re.sub(" / DN -[0-9][0-9]dB","",title)
        title=re.sub(" +"," ",title)
        title=" ".join(title.split())


        tempdict["title"]=title
        tempdict["useFile"]="True"
        tempdict["useTitle"]="True"
        tempdict["default"]="False"
        tempdict["langcode"]=code
        tempdict["lang"]=lang
        tempdict["Comment"]="No Comment"




        if re.search("Subtitle",currline)!=None:
            #normal subs
            tempdict["title"]=f"Subtitle:"
            if (sublang!=None and lang not in sublang) or sourcedex>0:
                tempdict["useFile"]="False"
            tempdict["useTitle"]="True"
            mediadict[str(key)]=tempdict
            continue
        if re.search("Audio",currline)!=None:
            #set default
            if defaultset==False:
                defaultset=True
                tempdict["default"]="True"
            else:
                tempdict["default"]="False"
            #set use file
            if audiolang!=None and lang not in audiolang:
                tempdict["useFile"]="False"
            elif sourcedex>0:
                tempdict["useFile"]="False"
            else:
                tempdict["useFile"]="True"
            if re.search("AC3 Core",title)!=None or re.search("AC3 Embedded",title)!=None :
                split=re.search('t.+ Embedded:',title)
                main=title[:split.start()+1]
                compat=title[split:]
                compat=f"Audio: Compatibility Track / Dolby Digital Audio /{compat}"
                tempdict2["title"]=compat
            #put compat after
            tempdict["title"]=title
            mediadict[str(key)]=tempdict


        #set variables for tempdict2/compat
        if tempdict2.get("title")!=None:
            tempdict2["useFile"]=tempdict["useFile"]
            tempdict2["useTitle"]=tempdict["useTitle"]
            tempdict2["default"]="False"
            tempdict2["langcode"]=tempdict["langcode"]
            tempdict2["lang"]=tempdict["lang"]
            tempdict2["Comment"]="No Comment"
            key2=randint(100000, 999999)
            mediadict[str(key2)]=tempdict2


    data.close()
    return mediadict,index
def getname(code,line,index):




    if re.search("Video",line)!=None and re.search("AVC",line)!=None:
        return f"{index}:00{index}-video.h264"
    if re.search("Video",line)!=None and re.search("HEVC",line)!=None:
        return f"{index}:00{index}-video.h265"
    if re.search("Video",line)!=None and re.search("VC-1",line)!=None:
        return f"{index}:00{index}-video.vc1"
    if re.search("Video",line)!=None and re.search("MPEG-2",line)!=None:
        return f"{index}:00{index}-video.mpeg2"
    if re.search("Audio",line)!=None:
        line=re.sub("Audio: ","",line)
        if re.search("Compatibility Track",line)!=None:
            codec="ac3"
            return f"{index}:00{index}-cmbt.{codec}"
        t=line.split("/")
        if re.search("LPCM",line)!=None:
            codec="flac"
        elif re.search("Master Audio",line)!=None:
            codec="dtsma"
        elif re.search("Dolby Digital",line)!=None:
            codec="ac3"

        elif re.search("DTS Audio",line)!=None:
            codec="dts"
        elif re.search("Dolby TrueHD Audio",line)!=None:
            codec="thd"


        return f"{index}:00{index}-{code}.{codec}"
    if re.search("Subtitle",line)!=None:

        line=re.sub("Subtitle: ","",line)
        t=line.split("/")
        t=t[0]
        #remove special characters
        return f"{index}:00{index}-{code}.sup"
def createTitle(data,show):
    video=None
    sound=None
    for key in data:



        if key=="chapters":
            continue

        mediadict=data[key]

        title=mediadict.get("title","")

        if re.search("Video: ",title)!=None:
            video=mediadict.get("title","")
        if re.search("Audio: ",title)!=None:
            sound=mediadict.get("title","")
            break


    if re.search("Video",video)!=None and re.search("AVC",video)!=None:
        vdcodec="AVC"
    elif re.search("Video",video)!=None and re.search("HEVC",video)!=None:
        vdcodec="HEVC"
    elif re.search("Video",video)!=None and re.search("VC-1",video)!=None:
        vdcodec="VC-1"
    elif re.search("Video",video)!=None and re.search("MPEG-2",video)!=None:
        vdcodec="MPEG2"
    if re.search("Audio",sound)!=None and re.search("LPCM",sound)!=None:
        adcodec="FLAC"
    elif re.search("Audio",sound)!=None and re.search("ATMOS",sound)!=None:
        adcodec="ATMOS"
    elif re.search("Audio",sound)!=None and re.search("DTS-HD Master",sound)!=None:
        adcodec="DTS-HD.MA"
    elif re.search("Audio",sound)!=None and re.search("Dolby TrueHD Audio",sound)!=None:
        adcodec="TrueHD"
    elif re.search("Dolby Digital",sound)!=None:
        adcodec="DTS-HD.MA"
    channels=sound.split("/")[1]
    name=guessit(show).get("title","")
    year=guessit(show).get("year","")
    height=guessit(show).get("screen_size","")
    name=re.sub(" ",".",name)
    title=f"{name}.{year}.{height}.BluRay..{vdcodec}.{adcodec}.{channels}"
    title=re.sub(" ","",title)
    print(title)
    correct=input("Title is it Correct?:")
    if correct!="y" and correct!="yes" and correct!="Yes" and correct!="YES" and correct!="Y":
        title_completer = WordCompleter([title])
        title = input('Enter Title: ', completer=title_completer,complete_while_typing=True)
    return title

def demux(bludir,data,show,index):
    filelist=[]
    media=[data["chapters"]]
    savekey=None
    videodict={}
    index=f"{index})"
    i=0
    for key in data:
        i=i+1
        if key=="chapters":
            continue
        if key=="video":
            videodict=data[key]
            continue
        if i==3:
            savekey=key
        line=data[key]["title"]
        code=data[key].get("langcode")
        if re.search("Compatibility",line)!=None:
            i=i-1
        t=getname(code,line,i)
        media.append(t)
        filename=t.split(":")[1]
        filelist.append(filename)
        data[key]["file"]=filename
        #USE first audio for video
    data["video"]["langcode"]=data[savekey]["langcode"]
    line=data["video"]["title"]
    t=getname(code,line,2)
    media.append(t)
    filename=t.split(":")[1]
    filelist.append(filename)
    data["video"]["file"]=filename

    path=winepath("-w",bludir,_tty_out=False)
    path=path.rstrip()
    # index=input("index: ")
    # if len(index)==0:
    #     index="1"




    success=False

    try:
        t=wine("/usr/local/bin/eac3to/eac3to.exe",path,index,media,"-demux","-progressnumbers" ,f"-log={show}.Eac3to.txt",_fg=True)
        success=True
    except:
        print("Error Trying without demux")
    if success==False:
        try:
            t=wine("/usr/local/bin/eac3to/eac3to.exe",path,index,media,"-progressnumbers" ,f"-log={show}.Eac3to.txt",_fg=True)
        except:
            print("Error Skipping Source")
            return False
    return data
def remux():
    media=[]
    movietitle=""
    chapters=""
    defaultset=False
    workdir=os.getcwd()
    f=open('options.json',"r")
    options= json.load(f)
    f.close()

    xml=t=fd('-t','f', '.xml',_tty_out=False).splitlines()[0]
    for key in options:
        if key=="movietitle":
            movietitle=options['movietitle']
            continue
        elif key=="chaptersdir":
            chapters=os.path.join(workdir,options["chaptersdir"],"chapters.txt")
            continue
        elif key=="videodir":
            videokey=options["videodir"]
            video=os.path.join(workdir,videokey,options[videokey]["video"]["file"])
            vidtitle=options[videokey]["video"]["title"].split(":")[1]
            vidtitle=re.sub("Audio: |Subtitles: |Video: ","",vidtitle)
            code=options[videokey]["video"]["langcode"]
            temp=["--language",f"0:{code}","--track-name",f"0:{vidtitle}",video]
            media.extend(temp)
            continue
        elif key=="audiorder" or key=="suborder":
            continue
        for mediakey in options[key]:


            if mediakey=="chapters" or mediakey=="video":
                continue
            mediadict=options[key][mediakey]

            useFile=mediadict.get("useFile","")
            file=mediadict.get("file","")
            code=mediadict.get("langcode","")
            default=mediadict.get("default","")
            useTitle=mediadict.get("useTitle","")
            title=mediadict.get("title","")
            mediatitle=re.sub("Audio: |Subtitle: |Video: ","",title)

            lang=Language.make(language=code).display_name()
            if re.search("Subtitle: ",title)!=None:
                if useTitle=="True":
                    temp=["--language",f"0:{code}","--compression", "0:none","--track-name",f"0:{mediatitle}"]

                else:
                    temp=["--language",f"0:{code}","--compression", "0:none"]
                if re.search("For non",title)!=None and code=="en":
                    temp.append("--forced-track")
                    temp.append("0:1")
                    title="Forced"



            elif re.search("Audio: ",title)!=None:

                if default=="True" and defaultset==False:
                    temp=["--language",f"0:{code}","--track-name",f"0:{mediatitle}","--default-track","0:True"]
                    defaultset=True
                else:
                    temp=["--language",f"0:{code}","--track-name",f"0:{mediatitle}"]

            temp.append(os.path.join(workdir,key,file))
            if useFile=="True":

                media.extend(temp)
    print(media)


    info=guessit(movietitle)
    t=info.get("title","")
    y=info.get("year","")
    mediatitle=f"{t} ({y})"


    try:
        t=mkvmerge("--title",mediatitle,"--chapters",chapters,"--output",f"{movietitle}.mkv","--global-tags",xml,media,_fg=True)
    except:
        print("Maybe Error")
    print("\n",f"{movietitle}.mkv")

    return movietitle
def remuxorder():
    media=[]
    movietitle=""
    chapters=""
    defaultset=False
    workdir=os.getcwd()
    f=open('options.json',"r")
    options= json.load(f)
    f.close()
    xml=t=fd('-t','f', '.xml',_tty_out=False).splitlines()[0]
    for key in options:
        if key=="movietitle":
            movietitle=options['movietitle']
            continue
        elif key=="chaptersdir":
            chapters=os.path.join(workdir,options["chaptersdir"],"chapters.txt")
            continue
        elif key=="videodir":
            videokey=options["videodir"]
            video=os.path.join(workdir,videokey,options[videokey]["video"]["file"])
            vidtitle=options[videokey]["video"]["title"]
            vidtitle=re.sub("Audio: |Subtitle: |Video: ","",vidtitle)
            code=options[videokey]["video"]["langcode"]
            temp=["--language",f"0:{code}","--track-name",f"0:{vidtitle}",video]
            media.extend(temp)
            continue
        elif key=="randomfolder" or key=="audiorder" or key=="suborder" :
            continue
    for item in options['audiorder']:
        key=item.split(":")[0]
        filedir=item.split(":")[1]
        mediadict=nested_lookup(key, options)[0]
        title=mediadict.get("title","")
        title=re.sub("Audio: |Subtitles: |Video: ","",title)

        useFile=mediadict.get("useFile")
        file=mediadict.get("file","")
        code=mediadict.get("langcode","")
        default=mediadict.get("default","")
        useTitle=mediadict.get("useTitle","")
        if default=="True" and defaultset==False:
            temp=["--language",f"0:{code}","--track-name",f"0:{title}","--default-track","0:1",os.path.join(workdir,filedir,file)]
            defaultset=True
        else:
            temp=["--language",f"0:{code}","--track-name",f"0:{title}",os.path.join(workdir,filedir,file)]
        if useFile=="True":
            media.extend(temp)
    for item in options['suborder']:
        key=item.split(":")[0]
        filedir=item.split(":")[1]
        mediadict=nested_lookup(key, options)[0]
        title=mediadict.get("title","")
        title=re.sub("Audio: |Subtitles: |Video: ","",title)
        useFile=mediadict.get("useFile")
        file=mediadict.get("file","")
        code=mediadict.get("langcode","")
        default=mediadict.get("default","")
        useTitle=mediadict.get("useTitle","")
        title=title.split(":")[1]
        if useTitle=="True":
            temp=["--language",f"0:{code}","--compression", "0:none","--track-name",f"0:{title}"]

        else:
            temp=["--language",f"0:{code}","--compression", "0:none"]
        if re.search("forced",file)!=None:
            temp.append("--forced-track")
            temp.append("0")


        temp.append(os.path.join(workdir,filedir,file))

        if useFile=="True":
            media.extend(temp)
    print(media)

    info=guessit(movietitle)
    t=info.get("title","")
    y=info.get("year","")
    mediatitle=f"{t} ({y})"
    try:
        t=mkvmerge("--title",mediatitle,"--chapters",chapters,"--output",f"{movietitle}.mkv","--global-tags",xml,media,_fg=True)
    except:
        print("Maybe Error")
    printInfo(f"{movietitle}.mkv")
    print("\n",f"{movietitle}.mkv")

    return movietitle
def printInfo(title):
    media_info = MediaInfo.parse(title,output="STRING",full=False)
    media_info=media_info.encode(encoding='utf8')
    media_info=media_info.decode('utf8', 'strict')
    t=open("mediainfo.txt","w")
    t.write(media_info)
    print(media_info)




def cleanup(data):

    video=None
    sound=None
    dex=0
    filelist=[]
    for key in data:
        dex=dex+1

        if key=="chapters":
            filelist.append("chapters.txt")
            continue



        mediadict=data[key]
        file=data[key].get("file")
        filelist.append(file)
        data[key]["size"]=humanize.naturalsize(os.path.getsize(file))

    for file in os.scandir("."):
        if re.search(".txt",file.name)!=None or  re.search(".",file.name)==None:
            continue
        elif re.search("forced captions",file.name)!=None:
            dex=dex+1
            lang=file.name.split(",")[1]
            code=langcodes.find(lang)
            code=  standardize_tag(code)
            forcedsubs=f"00{dex}-{code}.forced.sup"
            title=f"Subtitle: For non-{lang} parts"
            key=randint(100000, 999999)
            data[key]={"title":title,"useFile":"True","useTitle":"True","file":forcedsubs,"langcode":code}


            filelist.append(forcedsubs)
            t=wine(bdsup2sub,file.name,"--forced-only","-o",forcedsubs,_fg=True)




        elif file.name not in filelist:
            os.remove(file)


    return dict
def export_xml(show):
    details=guessit(show)
    title=details.get("title")
    imdbid=None
    if 'year' in details:
        title = "{} {}".format(title, details['year'])
    results = ia.search_movie(title)
    if len(results)==0 :
        print("Unable to find imdb")
        id = input("Enter Title or imdb(no tt) ")
        if re.search("tt",id)!=None:
            imdbid=ia.get_movie(id).movieID
        else:
            imdbid = ia.search_movie(id).movieID



    elif isinstance(results, list)!=True:
       imdbid=results.movieID
    else:
        counter=0
        accept=False
        print("Searching for movie/TV Show on IMDB","\n")
        while accept!="True"and accept!="Y" and accept!="Yes" and accept!="YES" and accept!="y" and counter<len(results):
           if counter==6:
               print("correct title not found")
               id = input("Enter imdb(no tt) ")
               imdbid=IMDb().get_movie(id).movieID

           print(results[counter]["title"]," ",results[counter]["year"])
           accept=input(" is this Search result correct?:")
           if len(accept)==0 or accept=="N" or accept=="No" or accept=="n" or accept=="NO":
                counter=counter+1
        if imdbid==None:
            imdbid=results[counter].movieID

        tmdb = movie.external(f"tt{imdbid}",f'imdb_id')
        if len(tmdb.get("movie_results"))!=0:
           tmdb=tmdb.get("movie_results")[0].get("id","")




    t=OrderedDict([('Tags', OrderedDict([('Tag', OrderedDict([('Targets', OrderedDict([('TargetTypeValue', '70')])), ('Simple', [OrderedDict([('Name', 'IMDB'), ('String', f"tt{imdbid}")]), OrderedDict([('Name', 'TMDB'), ('String', f'movie/{tmdb}')])])]))]))])
    w=open(f"{show}.xml","w")
    w.write(xmltodict.unparse(t, pretty=True))





if __name__ == "__main__":
    main()

