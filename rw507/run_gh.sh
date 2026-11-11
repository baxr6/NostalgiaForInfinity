#!/bin/bash
# GitHub runner version of run.sh: ARM YEAR SLICE, data in /w/data, markets offline (FT_MARKETS_FILE), output in rw507/out.
set -u; ARM=$1; Y=$2; S=$3; export RW=/w/rw507; O=$RW/out/$ARM/${Y}_$S
# arms named bk* run the NFI book config (6 slots, unlimited stake, 10,000 wallet)
CFG=rw.json; [[ $ARM == bk* ]] && CFG=book.json
mkdir -p $O/ud
read TR PAIRS < <(python3 -c "import json;d=json.load(open('$RW/slices.json'))['$Y'];print(d['range'],json.dumps(d['slices'][$S]).replace(' ',''))")
echo "{\"pairlists\":[{\"method\":\"StaticPairList\"}],\"exchange\":{\"name\":\"binance\",\"pair_whitelist\":$PAIRS,\"pair_blacklist\":[]}}" > $O/pl.json
echo "=== $ARM $Y s$S $TR start $(date -u +%T)"
freqtrade backtesting --config $RW/cfg/exampleconfig.json --config $RW/cfg/trading_mode-futures.json --config $RW/cfg/$CFG \
  --config $O/pl.json --strategy NostalgiaForInfinityX8_507 --strategy-path $RW/arms/$ARM --userdir $O/ud \
  --datadir /w/data/binance --timerange $TR --fee 0.0005 --cache none --export ${EXPORT:-trades} > $O/run.log 2>&1
RC=$?; ls $O/ud/backtest_results/*.zip >/dev/null 2>&1 || RC=9
grep -E "is not compatible|Removing" $O/run.log | head -3
if [ $RC -ne 0 ]; then tail -20 $O/run.log; echo "FAILED rc $RC"; exit 1; fi
python3 $RW/summ.py $O "$ARM" "$Y" "$S" | tee $O/row.tsv
rm -rf $O/ud/backtest_results/*.meta.json; echo "done $(date -u +%T)"
