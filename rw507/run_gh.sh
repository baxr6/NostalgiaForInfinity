#!/bin/bash
# GitHub runner version of run.sh: ARM YEAR SLICE, data in /w/data, markets offline (FT_MARKETS_FILE), output in rw507/out.
set -u; ARM=$1; Y=$2; S=$3; export RW=/w/rw507; O=$RW/out/$ARM/${Y}_$S
# arms named bk* run the NFI book config (6 slots, unlimited stake, 10,000 wallet)
CFG=rw.json; [[ $ARM == bk* ]] && CFG=book.json
mkdir -p $O/ud
# arms named speed*: paired populate_indicators CPU timing (rw507/speed), no backtest
if [[ $ARM == speed* ]]; then
  XC=${XC:-binance}; P=$RW/speed
  echo "{\"exchange\":{\"name\":\"$XC\",\"pair_whitelist\":[],\"pair_blacklist\":[]}}" > $O/pl.json
  nproc; lscpu | grep -E "Model name|^CPU\(s\)"
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python3 $P/ab_pop.py $O /w/data/$XC 40 \
    $RW/cfg/exampleconfig.json,$RW/cfg/trading_mode-futures.json,$RW/cfg/rw.json,$O/pl.json \
    up=$P/up302 c14=$P/c14 c14no1h=$P/c14no1h c507=$P/c507 c507no1h=$P/c507no1h 2>&1 | grep -v chown | tee $O/run.log
  exit ${PIPESTATUS[0]}
fi
# XC=bybit: Bybit data, slices and exchange (default binance, unchanged)
XC=${XC:-binance}; SL=slices.json; [ $XC = bybit ] && SL=slices_bybit.json; export GATE_LOG=$O/gate.json
read TR PAIRS < <(python3 -c "import json;d=json.load(open('$RW/$SL'))['$Y'];print(d['range'],json.dumps(d['slices'][$S]).replace(' ',''))")
# optional matrix.tr (period test): timerange override inside the same year data
[ -n "${TR_OVR:-}" ] && TR=$TR_OVR
echo "{\"pairlists\":[{\"method\":\"StaticPairList\"}],\"exchange\":{\"name\":\"$XC\",\"pair_whitelist\":$PAIRS,\"pair_blacklist\":[]}}" > $O/pl.json
echo "=== $ARM $Y s$S $TR start $(date -u +%T)"
freqtrade backtesting --config $RW/cfg/exampleconfig.json --config $RW/cfg/trading_mode-futures.json --config $RW/cfg/$CFG \
  --config $O/pl.json --strategy NostalgiaForInfinityX8_507 --strategy-path $RW/arms/$ARM --userdir $O/ud \
  --datadir /w/data/$XC --timerange $TR --fee 0.0005 --cache none --export ${EXPORT:-trades} > $O/run.log 2>&1
RC=$?; ls $O/ud/backtest_results/*.zip >/dev/null 2>&1 || RC=9
grep -E "is not compatible|Removing" $O/run.log | head -3
if [ $RC -ne 0 ]; then tail -20 $O/run.log; echo "FAILED rc $RC"; exit 1; fi
python3 $RW/summ.py $O "$ARM" "$Y" "$S" | tee $O/row.tsv
rm -rf $O/ud/backtest_results/*.meta.json; echo "done $(date -u +%T)"
