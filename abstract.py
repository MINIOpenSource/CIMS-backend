r=input;o=open
if __name__!="__main__":import sys as _;_.exit(0)
try:o(".installed").close();_i=True
except:_i=False
import argparse,asyncio,json,os,sys
from json import JSONDecodeError
for _r in["./logs","./Datas","./Datas/ClassPlan","./Datas/DefaultSettings","./Datas/Policy","./Datas/Subjects","./Datas/TimeLayout"]:
  try:os.mkdir(_r)
  except:...
for _f in["./settings.json"]+["./Datas/{}.json".format(name)for name in["client_status","clients","pre_register","profile_config"]]+["./Datas/{}/default.json".format(name)for name in["ClassPlan","DefaultSettings","Policy","Subjects","TimeLayout"]]:
  try:json.load(o(_f))
  except:o(_f,"w").write("{}")
try:json.load(o("project_info.json"))
except:json.dump({"name":"CIMS-backend","description":"ClassIsland Management Server on Python","author":"kaokao221","version":"1.1beta2","url":"https://github.com/MINIoSource/CIMS-backend"},o("project_info.json","w"))
import Datas,logger,BuildInClasses,QuickValues,ManagementServer
if _i:_s=json.load(o("settings.json"))
else:
  _s={}
  for part in["gRPC","api","command"]:
    _n=r("{} host and port used in ManagementPreset.json (formatted as {}://{}:{} and port must be given)(Enter directly to use default settings):".format(part,_s[part]["prefix"],_s[part]["host"],_s[part]["mp_port"]));_ps=True
    while _ps:
      try:
        if _n.startswith("http://"):print("HTTP is not safe and HTTPS recommended.\n"if not _n.startswith("http://localhost")else "",end="")
        if not _n.startswith(("https://","http://")):raise ValueError
        _s[part]["prefix"]=_n.split(":")[0] + "://";_s[part]["host"]=_n.split(":")[1][2:];_s[part]["mp_port"]=int(_n.split(":")[2]);_ps=False
      except KeyError:
        _n=r("Invalid r,retry:")
      except:
        if _n == "":_ps=False
        else:_n=r("Invalid r,retry:")
    if _n != "":
      _n=r("{part} listening port(Enter directly to use the same as above):".format(part=part));_ps=True
      while _ps:
        try:
          _s[part]["port"]=int(_n); _ps=False
        except ValueError:
          if _n == "":_s[part]["port"]=_s[part]["mp_port"];_ps=False
          else:_n=r("Invalid port,retry:")
    else:_s[part]["port"]=_s[part]["mp_port"]
  _n=r("Organization name:");_s["organization_name"]=_n if _n != "" else "CIMS Default Organization";json.dump(_s,o("settings.json","w"));o(".installed","w").close()
  async def refresh():await asyncio.gather(ManagementServer.command.Settings.refresh(),ManagementServer.api.Settings.refresh(),ManagementServer.gRPC.Settings.refresh());asyncio.run(refresh())
ps=argparse.ArgumentParser(description="ClassIsland Management Server Backend");ps.add_argument("-g","--generate-management-preset",action="store_true",help="Generate ManagementPreset.json on the program root.");ps.add_argument("-r","--restore",action="store_true",help="Restore,and delete all existed data");a=ps.parse_args()
async def start():await asyncio.gather(ManagementServer.gRPC.start(_s["gRPC"]["port"]),ManagementServer.api.start(_s["api"]["port"]),ManagementServer.command.start(_s["command"]["port"]),)
if a.restore:
  if r("Continue?(y/n with default n)") in ("y","Y"):import os;os.remove(".installed");os.remove("settings.json");os.remove("ManagementPreset.json")
elif a.generate_management_preset:json.dump({"ManagementServerKind":1,"ManagementServer":"{prefix}://{host}:{port}".format(prefix=_s["api"]["prefix"],host=_s["api"]["host"],port=_s["api"]["mp_port"]),"ManagementServerGrpc":"{prefix}://{host}:{port}".format(prefix=_s["gRPC"]["prefix"],host=_s["gRPC"]["host"],port=_s["gRPC"]["mp_port"])},o("ManagementPreset.json","w"))
else:print("\033[2JWelcome to use CIMS1.0v1sp0patch1");asyncio.run(start())