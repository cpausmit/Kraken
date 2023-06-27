#---------------------------------------------------------------------------------------------------
#
# ==== MAIN PARAMETERS FOR KRAKEN AGENTS ====
#
#---------------------------------------------------------------------------------------------------
# initialize Kraken base if not yet set
[ -z "$KRAKEN_BASE" ] && source /home/tier3/cmsprod/Tools/Kraken/setup.sh

# general agents info

export KRAKEN_AGENTS_BASE=/usr/local/Kraken/agents

export KRAKEN_AGENTS_LOG="/local/$KRAKEN_USER/Kraken/agents"

export KRAKEN_AGENTS_WORK="/home/tier3/$KRAKEN_USER/cms/jobs"
export KRAKEN_AGENTS_WWW="/home/tier3/$KRAKEN_USER/public_html/Kraken/agents"

# catalog/review agent parameters

export KRAKEN_REVIEW_CYCLE_HOURS=1
export KRAKEN_CATALOG_CYCLE_SECONDS=300
export KRAKEN_CLEANUP_CYCLE_SECONDS=300
