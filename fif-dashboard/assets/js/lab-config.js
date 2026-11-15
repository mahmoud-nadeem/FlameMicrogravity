/* Structured parameter boundary shared by offline commands and future model adapters. */
(function(){
  const F=window.FIF;
  F.labSchema={u:{min:0,max:8,unit:"cm/s"},d:{min:.1,max:5,unit:"cm²/s"},l:{min:10,max:100,unit:"cm"},t:{min:0,max:60,unit:"s"}};
  F.validateLabConfig=function(patch){
    if(!patch||typeof patch!=="object"||Array.isArray(patch))return {error:"Expected a parameter object."};
    for(const [key,value] of Object.entries(patch)){
      const rule=F.labSchema[key];
      if(!rule)return {error:"Unsupported parameter: "+key};
      if(typeof value!=="number"||!Number.isFinite(value)||value<rule.min||value>rule.max)return {error:key+" must be between "+rule.min+" and "+rule.max+" "+rule.unit+"."};
    }
    return {patch};
  };
  F.parseLabCommand=function(question,current){
    const q=question.toLowerCase();
    if(/oxygen|pressure|gravity|temperature|alarm|density|material|burn/.test(q))return {error:"This transport model supports flow, mixing, distance and time. That variable needs a different model."};
    const rules=[["u",/air\s*speed|air\s*flow|flow|speed/],["d",/mixing|dispersion/],["l",/distance|sensor position/],["t",/elapsed time|time/]];
    const patch={};let identified=false;
    for(const [key,pattern] of rules){
      if(!pattern.test(q))continue;identified=true;
      const explicit=q.match(new RegExp("(?:"+pattern.source+")\\s*(?:to|=|at|is)?\\s*(-?\\d+(?:\\.\\d+)?)"));
      if(explicit)patch[key]=+explicit[1];
      else if(key==="u"&&/still|stop/.test(q))patch[key]=0;
      else if(/double/.test(q))patch[key]=current[key]*2;
      else if(/halve|half/.test(q))patch[key]=current[key]/2;
      else if(/increase|higher|faster/.test(q))patch[key]=current[key]+(key==="u"?2:key==="d"?.5:10);
      else if(/decrease|lower|slower/.test(q))patch[key]=current[key]-(key==="u"?2:key==="d"?.5:10);
    }
    if(!identified&&/still air/.test(q))patch.u=0;
    if(!Object.keys(patch).length&&!/why|explain|happen|result|parameter|scenario/.test(q))return {error:"Try “set flow to 4”, “mixing to 2”, “distance to 60”, “time to 10” or “explain mixing”."};
    return F.validateLabConfig(patch);
  };
})();
