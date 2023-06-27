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
#params.register(
#    'doJEC', 
#    False, 
#    VarParsing.multiplicity.singleton,VarParsing.varType.bool,
#    'Flag to indicate whether or not to use the events weights from a Monte Carlo generator'
#)

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
    100000000
)

params.setDefault(
    'outputFile', 
    'test.root' 
)



# Define the process
process = cms.Process("LL")

# Parse command line arguments
print("Made it here")
params.parseArguments()
print("Not here")

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
    #SkipEvent = cms.untracked.vstring('ProductNotFound')
)

# How many events to process
process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(params.maxEvents) )

# Input EDM files
#list = FileUtils.loadListFromFile(options.inputFiles)
#readFiles = cms.untracked.vstring(*list)

print("reading files?")
if params.fileList == "none" : readFiles = params.inputFiles
else : 
    readFiles = cms.untracked.vstring( FileUtils.loadListFromFile (os.environ['CMSSW_BASE']+'/src/PhysicsTools/ScoutingNanoAOD/test/'+params.fileList) )
print("we shall see")
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
    #fileName = cms.string("scoutingData18.root")
    #fileName = cms.string("scoutingQCD500to700.root")
)

# Tree for the generator weights
process.gentree = cms.EDAnalyzer("LHEWeightsTreeMaker",
    lheInfo = cms.InputTag("externalLHEProducer"),
    genInfo = cms.InputTag("generator"),
    useLHEWeights = cms.bool(params.useWeights)
)


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

# Make tree
process.mmtree = cms.EDAnalyzer('ScoutingNanoAOD',
    doL1 = cms.bool(False),
    isMC = cms.bool(params.isMC),
    stageL1Trigger   = cms.uint32(2),

    hltProcess=cms.string("HLT"),
    bits          = cms.InputTag("TriggerResults", "", "HLT"),
    
    triggerresults   = cms.InputTag("TriggerResults", "", params.trigProcess),
    triggerConfiguration = cms.PSet(
    	hltResults            = cms.InputTag('TriggerResults','','HLT'),
    	l1tResults            = cms.InputTag(''),
    	daqPartitions         = cms.uint32(1),
    	l1tIgnoreMaskAndPrescale = cms.bool(False),
    	throw                 = cms.bool(False)
  	),
	ReadPrescalesFromFile = cms.bool( False ),
    AlgInputTag = cms.InputTag("gtStage2Digis"),
    l1tAlgBlkInputTag = cms.InputTag("gtStage2Digis"),
    l1tExtBlkInputTag = cms.InputTag("gtStage2Digis"),
    l1Seeds           = cms.vstring(L1Info),
    hltSeeds          = cms.vstring(HLTInfo),
	muons            = cms.InputTag("hltScoutingMuonPacker"),
	electrons        = cms.InputTag("hltScoutingEgammaPacker"),
    photons          = cms.InputTag("hltScoutingEgammaPacker"),
	pfcands          = cms.InputTag("hltScoutingPFPacker"),
	pfjets           = cms.InputTag("hltScoutingPFPacker"),
    vertices         = cms.InputTag("hltScoutingPrimaryVertexPacker","primaryVtx"),
    gens         = cms.InputTag("genParticles"),
	#vertices         = cms.InputTag("hltScoutingMuonPacker","displacedVtx"),
    #pileupinfo       = cms.InputTag("addPileupInfo"),
    #geneventinfo     = cms.InputTag("generator"),

    # for JEC corrections eventually
    #L1corrAK4_DATA = cms.FileInPath('CMSDIJET/DijetScoutingRootTreeMaker/data/80X_dataRun2_HLT_v12/80X_dataRun2_HLT_v12_L1FastJet_AK4CaloHLT.txt'),
    #L2corrAK4_DATA = cms.FileInPath('CMSDIJET/DijetScoutingRootTreeMaker/data/80X_dataRun2_HLT_v12/80X_dataRun2_HLT_v12_L2Relative_AK4CaloHLT.txt'),
    #L3corrAK4_DATA = cms.FileInPath('CMSDIJET/DijetScoutingRootTreeMaker/data/80X_dataRun2_HLT_v12/80X_dataRun2_HLT_v12_L3Absolute_AK4CaloHLT.txt'),
)
#process.Tracer = cms.Service("Tracer")

process.p = cms.Path(                  process.mmtree)
