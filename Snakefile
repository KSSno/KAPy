# KAPy Workflow
#
# This snakemake workflow handles the processing of data for use
# in Klimaatlas-like products. 
#
# The pipeline can be run using
#    > snakemake --cores 1 <target>
#
# A list of available target rules can be obatined using
#   > snakemake -S
#
# Workflow configuration options are set in config.yaml
#

import KAPy

#Setup-----------------------
#Load configuration 
config=KAPy.loadConfig()  

#Generate filename dicts
wf=KAPy.getWorkflow(config)

# Primary Variables---------------------------------
#Plural rule
rule primVars:
    input:
        list(wf['primVars'].keys())

#Singular rule
#Requires a bit of a hack with a lamba function to be able to both use a input function
#and feed additional arguments to the function
rule primVar_file:
    output:
        KAPy.buildPath(config,'primVars',"{pv}")
    input:
        lambda wildcards: wf['primVars'][KAPy.buildPath(config,'primVars',wildcards.pv)]
    run:
        KAPy.buildPrimVar(config,input,output)

# Secondary variables -------------------------
# "Secondary variables" are calculated as new variables derived from primary variables.  
# Good examples include FWI and PoteEvap. 
# TODO
        
# Bias correction -------------------
# TODO


# Indicators ---------------------------------
# Create a loop over the indicators that defines the singular and plural rules
# as well as the combined run

#Indicator singular rule
def ind_singular_rule(thisInd):
    rule:  
        name: f'i{thisInd["id"]}_file'
        output:
            KAPy.buildPath(config,'indicators',"{indFname}")
        input:
            lambda wildcards: 
                wf['indicators'][thisInd["id"]][ KAPy.buildPath(config,'indicators',wildcards.indFname)]
        run:
            KAPy.calculateIndicators(config=config,
                                     inFile=input,
                                     outFile=output,
                                     thisInd=thisInd)
                                     

#Indicator plural rule
def ind_plural_rule(thisInd):
    rule:
        name: f'i{thisInd["id"]}'
        input:
            list(wf['indicators'][thisInd['id']].keys())
            
for thisInd in config['indicators'].values():
    ind_singular_rule(thisInd)
    ind_plural_rule(thisInd)

#Run all indicators    
rule indicators:
    input:
        [list(thisInd.keys()) for thisInd in wf['indicators'].values()]

'''           
                                               
# Regridding  ---------------------------------
# Combining everything into an ensemble requires that they are all on a common grid
# This is not always the case, and so we add a regridding step prior to ensemble calculation
rule regrid:
    input:
        expand(KAPy.buildPath(config,'gridded','{stem}.nc'),
               stem=glob_wildcards(KAPy.buildPath(config,'indicators','{stem}.nc')).stem)

rule regrid_file:
    output:
        KAPy.buildPath(config,'gridded','{stem}.nc')
    input:
        KAPy.buildPath(config,'indicators','{stem}.nc')
    run:
        KAPy.regrid(config,input,output)

'''

# Enssemble Statistics ---------------------------------
# Now we can combine them into ensembles
#Plural rule
rule ensstats:
    input:
        list(wf['ensstats'].keys())

#Singular rule
rule ensstats_file:
    output:
        KAPy.buildPath(config,'ensstats',"{es}")
    input:
        lambda wildcards: wf['ensstats'][KAPy.buildPath(config,'ensstats',wildcards.es)]
    run:
        KAPy.generateEnsstats(config,input,output)


#Areal statistics------------------
#Areal statistics can be calculated for both the enssemble statistics and the
#individual ensemble members - these options can be turned on and off as required
#via the configuration options. 
#Plural rule
rule arealstats:
    input:
        list(wf['arealstats'].keys())

#Singular rule
rule arealstats_file:
    output:
        KAPy.buildPath(config,'arealstats','{arealstats}')
    input:
        lambda wildcards: wf['arealstats'][KAPy.buildPath(config,'arealstats',wildcards.arealstats)]
    run:
        KAPy.generateArealstats(config,input,output)

# Outputs ---------------------------------
# Notebooks, amongst other things
#Plural rule
rule notebooks:
    input:
        list(wf['notebooks'].keys())

#Singular rule
rule notebook_file:
    output:
        KAPy.buildPath(config,'notebooks','{notebook}')
    input:
        lambda wildcards: wf['notebooks'][KAPy.buildPath(config,'notebooks',wildcards.notebook)]
    shell:
        "jupyter nbconvert --execute --to html --TemplateExporter.exclude_input=True --output-dir=. --output='{output}' {input[0]}"


#All-------------------
rule all:
    input:
        wf['all']
    default_target: True

