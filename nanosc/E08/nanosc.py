import FWCore.ParameterSet.Config as cms
import FWCore.Utilities.FileUtils as FileUtils
import os

# Set parameters externally 
from FWCore.ParameterSet.VarParsing import VarParsing
params = VarParsing('analysis')

params.register(
    'isMC', 
    False, 
    VarParsing.multiplicity.singleton,VarParsing.varType.bool,
    'Flag to indicate whether the sample is simulation or data'
)

params.register(
    'useWeights', 
    False, 
    VarParsing.multiplicity.singleton,VarParsing.varType.bool,
    'Flag to indicate whether or not to use the events weights from a Monte Carlo generator'
)

params.register(
    'filterTrigger', 
    False, 
    VarParsing.multiplicity.singleton,VarParsing.varType.bool,
    'Flag to indicate whether or not to ask the event to fire a trigger used in the analysis'
)

params.register(
    'filterMuons', 
    False, 
    VarParsing.multiplicity.singleton,VarParsing.varType.bool,
    'Flag to indicate whether or not to ask the event to contain at least two muons'
)

params.register(
    'reducedInfo', 
    False, 
    VarParsing.multiplicity.singleton,VarParsing.varType.bool,
    'Flag to indicate whether or not to store just the reduced information'
)

params.register(
    'trigProcess', 
    'HLT', 
    VarParsing.multiplicity.singleton,VarParsing.varType.string,
    'Process name for the HLT paths'
)

params.register(
    'GlobalTagData', 
    #'101X_dataRun2_HLT_v7',
    '101X_dataRun2_Prompt_v11', 
    VarParsing.multiplicity.singleton,VarParsing.varType.string,
    'Process name for the HLT paths'
)

params.register(
    'GlobalTagMC', 
    '102X_upgrade2018_realistic_v15', 
    VarParsing.multiplicity.singleton,VarParsing.varType.string,
    'Process name for the HLT paths'
)# check this

params.register(
    'xsec', 
    0.001, 
    VarParsing.multiplicity.singleton,VarParsing.varType.float,
    'Cross-section for a Monte Carlo Sample'
)#fix this

params.register(
    'fileList', 
    'none', 
    VarParsing.multiplicity.singleton,VarParsing.varType.string,
    'input list of files'
)

params.setDefault(
    'maxEvents', 
    -1
)

params.setDefault(
    'outputFile', 
    'test.root' 
)

params.register(
  "era",
  "2018",
  VarParsing.multiplicity.singleton,VarParsing.varType.string,
  "era"
)

params.register(
    'signal', 
    False, 
    VarParsing.multiplicity.singleton,VarParsing.varType.bool,
    'Flag to indicate whether or not signal is run'
)
#params.register(
#    'runScouting', 
#    True, 
#    VarParsing.multiplicity.singleton,VarParsing.varType.bool,
#    'Flag to indicate whether or not signal is run'
#)
#params.register(
#    'runOffline', 
#    False, 
#    VarParsing.multiplicity.singleton,VarParsing.varType.bool,
#    'Flag to indicate whether or not signal is run'
#)

#params.register(
#    'monitor', 
#    False, 
#    VarParsing.multiplicity.singleton,VarParsing.varType.bool,
#    'Flag to indicate whether or not moninor is run'
#)

# Define the process
process = cms.Process("LL")

# Parse command line arguments
params.parseArguments()

# Message Logger settings
process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.destinations = ['cout', 'cerr']
process.MessageLogger.cerr.FwkReport.reportEvery = 1000 
#process.MessageLogger.cerr.threshold = 'INFO'
#process.MessageLogger.cerr.INFO = cms.untracked.PSet(
#    limit = cms.untracked.int32(-1)
#)

# Set the process options -- Display summary at the end, enable unscheduled execution
process.options = cms.untracked.PSet( 
    allowUnscheduled = cms.untracked.bool(True),
    wantSummary      = cms.untracked.bool(True),
    Rethrow = cms.untracked.vstring("ProductNotFound"), # make this exception fatal
    #Rethrow = cms.untracked.vstring()
    FailPath = cms.untracked.vstring("ProductNotFound")
    #SkipEvent = cms.untracked.vstring('ProductNotFound')
)

# How many events to process
process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(params.maxEvents) )

# Input EDM files
#list = FileUtils.loadListFromFile(options.inputFiles)
#readFiles = cms.untracked.vstring(*list)

if params.fileList == "none" : readFiles = params.inputFiles
else : 
    readFiles = cms.untracked.vstring( FileUtils.loadListFromFile (os.environ['CMSSW_BASE']+'/src/PhysicsTools/ScoutingNanoAOD/test/'+params.fileList) )
process.source = cms.Source("PoolSource",
	fileNames = cms.untracked.vstring(readFiles) 
)

# Load the standard set of configuration modules
process.load('Configuration.StandardSequences.Services_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff')
process.load('Configuration.StandardSequences.GeometryDB_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')

##--- l1 stage2 digis ---
process.load("EventFilter.L1TRawToDigi.gtStage2Digis_cfi")
process.gtStage2Digis.InputLabel = cms.InputTag( "hltFEDSelectorL1" )
process.load('PhysicsTools.PatAlgos.producersLayer1.patCandidates_cff')

# Load the global tag
from Configuration.AlCa.GlobalTag import GlobalTag
if params.isMC : 
    process.GlobalTag.globaltag = params.GlobalTagMC
else :
    process.GlobalTag.globaltag = params.GlobalTagData

# Define the services needed for the treemaker
process.TFileService = cms.Service("TFileService", 
    fileName = cms.string(params.outputFile)
)

# Tree for the generator weights
process.gentree = cms.EDAnalyzer("LHEWeightsTreeMaker",
    lheInfo = cms.InputTag("externalLHEProducer"),
    genInfo = cms.InputTag("generator"),
    useLHEWeights = cms.bool(params.useWeights)
)

# get rho producer
#runRho = not(params.isMC and params.era=="2016") 
#if(runRho):
#  if params.era=="2015":
#    runRho = False
##if(params.runScouting):
#if(runRho):
#  process.fixedGridRhoFastjetAllScouting = cms.EDProducer("FixedGridRhoProducerFastjetScouting",
#      pfCandidatesTag = cms.InputTag("hltScoutingPFPacker"),
#      electronsTag = cms.InputTag("hltScoutingEgammaPacker"),
#      maxRapidity = cms.double(5.0),
#      gridSpacing = cms.double(0.55),
#  )
#print("RUNNNING TEST| isMC %d| signal %d| data %d| scouting %d| offline %d")



HLTInfo = [
    "DST_DoubleMu1_noVtx_CaloScouting_v*",
    "DST_DoubleMu3_noVtx_CaloScouting_v*",
    "DST_DoubleMu3_noVtx_Mass10_PFScouting_v*",
    "DST_L1HTT_CaloScouting_PFScouting_v*",
    "DST_CaloJet40_CaloScouting_PFScouting_v*",
    "DST_HT250_CaloScouting_v*",
    "DST_HT410_PFScouting_v*",
    "DST_HT450_PFScouting_v*"]
L1Info = [
    'L1_HTT200er',
    'L1_HTT255er',
    'L1_HTT280er',
    'L1_HTT320er',
    'L1_HTT360er',
    'L1_HTT400er',
    'L1_HTT450er',
    'L1_SingleJet180',
    'L1_SingleJet200',
    'L1_DoubleJet30er2p5_Mass_Min300_dEta_Max1p5',
    'L1_DoubleJet30er2p5_Mass_Min330_dEta_Max1p5',
    'L1_DoubleJet30er2p5_Mass_Min360_dEta_Max1p5',
    'L1_ETT2000']
runSig = False
#if "SUEP" in readFiles[0]:
#  runSig = True
#if params.signal:
#  runSig = True

process.mmtree = cms.EDAnalyzer('ScoutingNanoAOD',
    doL1              = cms.bool(False),
    doData            = cms.bool(not params.isMC and not params.signal),
    doSignal          = cms.bool(runSig), 
    isMC              = cms.bool(params.isMC),
    #monitor           = cms.bool(params.monitor),
    era_16            = cms.bool(params.era == "2016"),
    #runScouting          = cms.bool(params.runScouting),
    #runOffline          = cms.bool(params.runOffline),
    #runScouting          = cms.bool(not(params.isMC and params.era == 2016)), #always run scouting except 2016MC
    #runOffline          = cms.bool(params.isMC and not params.signal), #only run offline for QCD
    stageL1Trigger    = cms.uint32(2),

    hltProcess=cms.string("HLT"),
    bits              = cms.InputTag("TriggerResults", "", "HLT"),
    
    triggerresults   = cms.InputTag("TriggerResults", "", params.trigProcess),
    triggerConfiguration = cms.PSet(
    	hltResults               = cms.InputTag('TriggerResults','','HLT'),
    	l1tResults               = cms.InputTag(''),
    	daqPartitions            = cms.uint32(1),
    	l1tIgnoreMaskAndPrescale = cms.bool(False),
    	throw                    = cms.bool(False)
  	),
    ReadPrescalesFromFile = cms.bool( False ),
    AlgInputTag = cms.InputTag("gtStage2Digis"),
    l1tAlgBlkInputTag = cms.InputTag("gtStage2Digis"),
    l1tExtBlkInputTag = cms.InputTag("gtStage2Digis"),
    l1Seeds           = cms.vstring(L1Info),
    hltSeeds          = cms.vstring(HLTInfo),
    muons             = cms.InputTag("hltScoutingMuonPacker"),
    electrons         = cms.InputTag("hltScoutingEgammaPacker"),
    photons           = cms.InputTag("hltScoutingEgammaPacker"),
    pfcands           = cms.InputTag("hltScoutingPFPacker"),
    pfjetsoff         = cms.InputTag("ak4PFJets"),
    pfjets            = cms.InputTag("hltScoutingPFPacker"),
    vertices_2016     = cms.InputTag("hltScoutingPFPacker",""), #Will try 2016 Packer and default to others if failed
    vertices          = cms.InputTag("hltScoutingPrimaryVertexPacker","primaryVtx"),
    offlineTracks     = cms.InputTag("particleFlow"),
    offlineTracks2     = cms.InputTag("packedPFCandidates"),
    #offlineTracks     = cms.InputTag("generalTracks"),
    pileupinfo        = cms.InputTag("addPileupInfo"),
    pileupinfo_sig    = cms.InputTag("slimmedAddPileupInfo"),
    geneventinfo     = cms.InputTag("generator"),
    gens              = cms.InputTag("genParticles"),
    gens_sig          = cms.InputTag("genParticles"),
    #gens_sig          = cms.InputTag("prunedGenParticles"),
    #rho               = cms.InputTag("fixedGridRhoFastjetAllScouting"),
    rho2              = cms.InputTag("hltScoutingPFPacker","rho"),
#    genLumi            = cms.InputTag("generator"),

    # for JEC corrections eventually
    #L1corrAK4_DATA    = cms.FileInPath('CMSDIJET/DijetScoutingRootTreeMaker/data/80X_dataRun2_HLT_v12/80X_dataRun2_HLT_v12_L1FastJet_AK4CaloHLT.txt'),
    #L2corrAK4_DATA    = cms.FileInPath('CMSDIJET/DijetScoutingRootTreeMaker/data/80X_dataRun2_HLT_v12/80X_dataRun2_HLT_v12_L2Relative_AK4CaloHLT.txt'),
    #L3corrAK4_DATA    = cms.FileInPath('CMSDIJET/DijetScoutingRootTreeMaker/data/80X_dataRun2_HLT_v12/80X_dataRun2_HLT_v12_L3Absolute_AK4CaloHLT.txt'),
)
#process.Tracer = cms.Service("Tracer")

# add any intermediate modules to this task list
# then unscheduled mode will call them automatically when the final module (mmtree) consumes their products
#if(params.runScouting):
#if(runRho):
#  process.myTask = cms.Task(process.fixedGridRhoFastjetAllScouting)

if(params.isMC):
#if(runSig or (params.isMC and not params.era=="2016")):
#if(runSig):
#if(params.signal):
  #print("test1",runSig,params.isMC,params.era,(params.isMC and not params.era=="2016"))
  from PhysicsTools.PatUtils.l1PrefiringWeightProducer_cfi import l1PrefiringWeightProducer
  process.prefiringweight = l1PrefiringWeightProducer.clone(
  ThePhotons           = cms.InputTag("hltScoutingEgammaPacker"),
  TheMuons             = cms.InputTag("hltScoutingMuonPacker"),
  TheJets            = cms.InputTag("hltScoutingPFPacker"),
  #TheJets = cms.InputTag("slimmedJets"), #this should be the slimmedJets collection with up to date JECs 
  #TheJets = cms.InputTag("updatedPatJetsUpdatedJEC"), #this should be the slimmedJets collection with up to date JECs 
  DataEraECAL = cms.string("2017BtoF"), #Use 2016BtoH for 2016
  DataEraMuon = cms.string("20172018"), #Use 2016 for 2016
  UseJetEMPt = cms.bool(False),
  PrefiringRateSystematicUnctyECAL = cms.double(0.2),
  PrefiringRateSystematicUnctyMuon = cms.double(0.2)
  )
  process.p = cms.Path(process.prefiringweight* process.mmtree)
else:
  process.p = cms.Path(process.mmtree)
#if(params.runScouting):
#if(runRho):
#  process.p.associate(process.myTask)
