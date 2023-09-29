#Snakemake configuration file

import KAPy
import os
import re
import glob

#Load a configuration
configfile: "config.yaml"
#config=KAPy.helpers.loadConfig()  #Debugging

esgf=KAPy.configs.loadConfig('configs/Ghana','ESGF')
scenarioList=['rcp26','rcp45','rcp85']

rule URLs:
    shell:
        "python3 ./KAPy/download/searchESGF.py"


rule downloads:
    input: 
        expand(os.path.join('scratch','2b.OPeNDAP_data','{fname}'),
               fname=[re.sub('.url','',x) 
               
               
               
                      for x in os.listdir(os.path.join('scratch',
                                                       '2a.OPeNDAP_URLs'))])
        
rule download:
    output:
        os.path.join('scratch','2b.OPeNDAP_data','{fname}.nc')
    input:
        os.path.join('scratch','2a.OPeNDAP_URLs','{fname}.nc.url')
    run:
        KAPy.download.ESGF(input,output,config,esgf)
        
        
rule xarrays:
    run:
        KAPy.xarrayObjects.makeDatasets(os.path.join('scratch','2b.OPeNDAP_data'),
                     os.path.join('scratch','3.xarrays'),
                     config)
        
rule indicators:
    input:
        expand(os.path.join('scratch','4.indicators','i101_{stem}.nc'),
        stem=[re.sub('tas_|.pkl','',x) \
              for x in                  os.listdir(os.path.join('scratch','3.xarrays'))])
        
        
rule index101:
    output:
        os.path.join('scratch','4.indicators','i101_{stem}.nc')
    input:
        os.path.join('scratch','3.xarrays','tas_{stem}.pkl')
    run:
        KAPy.indicators.index101(input[0],output[0],config)

rule regridded:
    input:
        expand(os.path.join('scratch','5.regrid','{stem}'),
               stem=os.listdir(os.path.join('scratch','4.indicators')))

rule regrid:
    output:
        os.path.join('scratch','5.regrid','{stem}.nc')
    input:
        os.path.join('scratch','4.indicators','{stem}.nc')
    run:
        KAPy.xarrayObjects.regrid(input,output,config)
        
rule ensstats:
    input:
        expand(os.path.join('scratch','6.ensstat','i101_ensstat_{scenario}.nc'),
               scenario=scenarioList)

        
for sc in scenarioList:
    rule:
        name: f'ensstat_{sc}'
        output:
            os.path.join('scratch','6.ensstat',f'i101_ensstat_{sc}.nc')
        input:
            glob.glob(os.path.join('scratch','5.regrid',f'i101_*_{sc}_*.nc'))
        run:
            KAPy.xarrayObjects.generateEnsstats(input,output,config)
        