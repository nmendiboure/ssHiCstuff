#!/usr/bin/bash

base_dir="/home/nicolas/Documents/Projects/ssHiC"
script="${base_dir}/hic_ssdna/sshic/pipeline.py"

fragments="${base_dir}/data/samples/inputs/fragments_list_S288c_DSB_LY_Capture_artificial_DpnIIHinfI.txt"
oligos="${base_dir}/data/samples/inputs/capture_oligo_positions.csv"
additional="${base_dir}/data/samples/inputs/additional_probe_groups.tsv"
centromeres="${base_dir}/data/samples/inputs/S288c_chr_centro_coordinates.tsv"
binning="1000 2000 3000 5000 10000 20000 40000 50000 80000 100000"
ws_centros=150000
ws_telos=150000
excluded_chr="chr2 chr3 chr5 2_micron mitochondrion chr_artificial"

run_pipeline() {
    python3 "$script" -s "$sample" \
                      -f "$fragments" \
                      -o "$oligos" \
                      -c "$centromeres" \
                      -r "$reference" \
                      -b $binning \
                      -a "$additional" \
                      --window-size-centros $ws_centros \
                      --window-size-telos $ws_telos \
                      --excluded-chr "$excluded_chr" \
                      --exclude-probe-chr
}

samples_dir="${base_dir}/data/samples/AD162_AD407"
refs_dir="${base_dir}/data/samples/inputs/refs"

samples=(
    "${samples_dir}/AD162_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD163_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD164_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD165_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD166_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD167_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD168_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD169_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD206_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD207_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD208_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD209_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD210_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD211_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD212_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD213_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD233_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD234_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD235_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD236_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD237_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD238_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD239_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD240_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD241_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD242_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD243_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD244_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD245_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD246_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD247_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD248_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD257_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD258_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD259_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD260_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD289_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD290_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD291_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD292_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD293_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD294_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD295_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD296_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD297_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD298_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD299_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD300_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD301_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD302_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD342_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD343_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD344_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD345_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD346_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD347_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt"
    "${samples_dir}/AD401_S288c_DSB_LY_Capture_artificial_cutsite_PCRfree_q20.txt"
    "${samples_dir}/AD402_S288c_DSB_LY_Capture_artificial_cutsite_PCRfree_q20.txt"
    "${samples_dir}/AD403_S288c_DSB_LY_Capture_artificial_cutsite_PCRfree_q20.txt"
    "${samples_dir}/AD404_S288c_DSB_LY_Capture_artificial_cutsite_PCRfree_q20.txt"
    "${samples_dir}/AD405_S288c_DSB_LY_Capture_artificial_cutsite_PCRfree_q20.txt"
    "${samples_dir}/AD406_S288c_DSB_LY_Capture_artificial_cutsite_PCRfree_q20.txt"
    "${samples_dir}/AD407_S288c_DSB_LY_Capture_artificial_cutsite_PCRfree_q20.txt"
    "${samples_dir}/AD407_S288c_DSB_LY_Capture_artificial_cutsite_PCRfree_q20.txt"

)

references=(
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT2h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT2h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT2h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT2h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT2h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT2h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT2h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT2h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT2h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT2h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT2h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT2h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT4h_v2.tsv"
  "${refs_dir}/ref_WT4h_v2.tsv"
  "${refs_dir}/ref_WT4h_v2.tsv"
  "${refs_dir}/ref_WT4h_v2.tsv"
  "${refs_dir}/ref_WT4h_v2.tsv"
  "${refs_dir}/ref_WT4h_v2.tsv"
  "${refs_dir}/ref_WT2h_v2.tsv"
  "${refs_dir}/ref_WT4h_v2.tsv"
  "${refs_dir}/ref_WT2h_v2.tsv"
  "${refs_dir}/ref_WT4h_v2.tsv"
  "${refs_dir}/ref_WT2h_v2.tsv"
  "${refs_dir}/ref_WT4h_v2.tsv"
  "${refs_dir}/ref_WT2h_v2.tsv"
  "${refs_dir}/ref_WT4h_v2.tsv"
  "${refs_dir}/ref_WT2h_v2.tsv"
  "${refs_dir}/ref_WT4h_v2.tsv"
  "${refs_dir}/ref_WT2h_v2.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT4h_v1.tsv"
  "${refs_dir}/ref_WT2h_v3.tsv"
  "${refs_dir}/ref_WT4h_v3.tsv"
  "${refs_dir}/ref_WT2h_v2.tsv"
  "${refs_dir}/ref_WT4h_v2.tsv"
  "${refs_dir}/ref_WT4h_v3.tsv"
  "${refs_dir}/ref_WT2h_AD403.tsv"
  "${refs_dir}/ref_WT4h_AD402.tsv"
  "${refs_dir}/ref_WT4h_AD404.tsv"
)



for ((i=0; i<${#samples[@]}; i++)); do
    sample="${samples[i]}"
    reference="${references[i]}"
    run_pipeline
done