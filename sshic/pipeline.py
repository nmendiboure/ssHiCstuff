import os
from os.path import join, dirname
import itertools
import argparse
import shutil
import pandas as pd
from typing import List, Optional

from core.filter import filter_contacts
from core.probe2fragment import associate_probes_to_fragments
from core.coverage import coverage
from core.fragments import organize_contacts
from core.statistics import get_stats, compare_to_wt
from core.binning import rebin_contacts
from core.weight import weight_mutant
from core.aggregated import aggregate


class PathBundle:
    def __init__(self, sample_sparse_file_path: str, reference_path_list: List[str] = None):

        self.sample_sparse_file_path = sample_sparse_file_path
        # self.samp_id = re.match(r"AD\d+[A-Z]*", sample_sparse_file_path.split("/")[-1]).group()
        self.samp_id = sample_sparse_file_path.split("/")[-1].split("_")[0]
        parent_dir = dirname(dirname(sample_sparse_file_path))
        outputs_dir = join(parent_dir, "outputs")

        self.sample_dir = join(outputs_dir, self.samp_id)
        if 'pcrfree' in self.sample_sparse_file_path.split("/")[-1].lower():
            self.sample_output_dir = join(self.sample_dir, "pcrfree")
        elif 'pcrdupkept' in self.sample_sparse_file_path.split("/")[-1].lower():
            self.sample_output_dir = join(self.sample_dir, "pcrdupkept")
        else:
            self.sample_output_dir = self.sample_dir

        self.sample_inputs_dir = join(self.sample_dir, "inputs")
        self.not_weighted_dir = join(self.sample_output_dir, "not_weighted")

        os.makedirs(self.sample_dir, exist_ok=True)
        os.makedirs(self.sample_output_dir, exist_ok=True)
        os.makedirs(self.sample_inputs_dir, exist_ok=True)
        os.makedirs(self.not_weighted_dir, exist_ok=True)

        self.filtered_contacts_input = join(self.sample_output_dir, self.samp_id + "_filtered.tsv")
        self.cover = join(self.sample_output_dir, self.samp_id + "_coverage_per_fragment.bedgraph")
        self.unbinned_contacts_input = join(self.not_weighted_dir, self.samp_id+"_unbinned_contacts.tsv")
        self.unbinned_frequencies_input = join(self.not_weighted_dir, self.samp_id+"_unbinned_frequencies.tsv")
        self.global_statistics_input = join(self.sample_output_dir, f"{self.samp_id}_global_statistics.tsv")

        self.wt_references_path = []
        self.wt_references_name = []
        self.weighted_dirs = []
        if reference_path_list:
            for ref_path in reference_path_list:
                ref_name = ref_path.split("/")[-1].split(".")[0]
                self.wt_references_path.append(ref_path)
                self.wt_references_name.append(ref_name)
                weighted_dir = join(self.sample_output_dir, f"weighted_{ref_name}")
                self.weighted_dirs.append(weighted_dir)
                os.makedirs(weighted_dir, exist_ok=True)


class AggregateParams:
    def __init__(self, window_size_centro, window_size_telos, excluded_probe_chr, excluded_chr_list):
        self.window_size_centromeres = window_size_centro
        self.window_size_telomeres = window_size_telos
        self.excluded_probe_chr = excluded_probe_chr
        self.excluded_chr_list = excluded_chr_list


def check_and_run(output_path, func, *args):
    if not os.path.exists(output_path):
        func(*args)


def copy_file(source_path, destination_path):
    try:
        shutil.copy(source_path, destination_path)
        print(f"File {source_path.split('/')[-1]} copied successfully.")
    except IOError as e:
        print(f"Unable to copy file. Error: {e}")


def pipeline(
    path_bundle: PathBundle,
    oligos_path: str,
    fragments_list_path: str,
    centromeres_coordinates_path: str,
    binning_size_list: List[int],
    aggregate_params: AggregateParams,
    additional_groups: Optional[str] = None
):
    print(f" -- Sample {path_bundle.samp_id} -- \n")

    copy_file(fragments_list_path, path_bundle.sample_inputs_dir)
    copy_file(centromeres_coordinates_path, path_bundle.sample_inputs_dir)
    copy_file(additional_groups, path_bundle.sample_inputs_dir)
    copy_file(oligos_path, path_bundle.sample_inputs_dir)
    copy_file(path_bundle.sample_sparse_file_path, path_bundle.sample_inputs_dir)
    for rp in path_bundle.wt_references_path:
        copy_file(rp, path_bundle.sample_inputs_dir)

    print("\n")

    print(f"Filter contacts \n")
    check_and_run(
        path_bundle.filtered_contacts_input, filter_contacts, oligos_path,
        fragments_list_path, path_bundle.sample_sparse_file_path, path_bundle.sample_output_dir)

    print(f"Associate the fragment name to probe where it is located \n")
    associate_probes_to_fragments(fragments_list_path, oligos_path)

    print(f"Make the coverage \n")
    check_and_run(
        path_bundle.cover, coverage, path_bundle.sample_sparse_file_path,
        fragments_list_path, path_bundle.sample_output_dir)

    print(f"Organize the contacts between probe fragments and the rest of the genome 'unbinned tables' \n")
    check_and_run(
        path_bundle.unbinned_contacts_input, organize_contacts, path_bundle.filtered_contacts_input,
        oligos_path, centromeres_coordinates_path, path_bundle.not_weighted_dir, additional_groups)

    print(f"Make basic statistics on the contacts (inter/intra chr, cis/trans, ssdna/dsdna etc ...) \n")
    check_and_run(
        path_bundle.global_statistics_input, get_stats, path_bundle.unbinned_contacts_input,
        path_bundle.sample_sparse_file_path, oligos_path, path_bundle.sample_output_dir)

    for rp, rn, rd in zip(path_bundle.wt_references_path, path_bundle.wt_references_name, path_bundle.weighted_dirs):
        print(f"Compare the capture efficiency with that of a wild type (may be another sample) \n")
        compare_to_wt(
            statistics_path=path_bundle.global_statistics_input,
            reference_path=rp,
            wt_ref_name=rn)

        print(f"Weight the unbinned contacts and frequencies tables by the efficiency score got on step ahead \n")
        weight_mutant(
            statistics_path=path_bundle.global_statistics_input, wt_ref_name=rn,
            contacts_path=path_bundle.unbinned_contacts_input, frequencies_path=path_bundle.unbinned_frequencies_input,
            binned_type="unbinned", output_dir=rd, additional_path=additional_groups)

    print(f"Rebin and weight the unbinned tables (contacts and frequencies) at : \n")
    for bn in binning_size_list:
        bin_suffix = str(bn // 1000) + "kb"
        print(bin_suffix)
        rebin_contacts(
            contacts_unbinned_path=path_bundle.unbinned_contacts_input,
            chromosomes_coord_path=centromeres_coordinates_path, oligos_path=oligos_path, bin_size=bn,
            output_dir=path_bundle.not_weighted_dir, additional_path=additional_groups)

        binned_contacts_input = \
            join(path_bundle.not_weighted_dir, path_bundle.samp_id + f"_{bin_suffix}_binned_contacts.tsv")
        binned_frequencies_input = \
            join(path_bundle.not_weighted_dir, path_bundle.samp_id + f"_{bin_suffix}_binned_frequencies.tsv")

        for rn, rd in zip(path_bundle.wt_references_name, path_bundle.weighted_dirs):
            weight_mutant(
                statistics_path=path_bundle.global_statistics_input, wt_ref_name=rn,
                contacts_path=binned_contacts_input, frequencies_path=binned_frequencies_input,
                binned_type=f"{bin_suffix}_binned", output_dir=rd,
                additional_path=additional_groups)

    print("\n")

    regions = ["centromeres", "telomeres"]
    weights_dir = [rd for rd in path_bundle.weighted_dirs] + [path_bundle.not_weighted_dir]
    normalization = [True, False]

    param_combinations = list(itertools.product(regions, weights_dir, normalization))
    for region, weight_dir, is_normalized in param_combinations:
        binned_10kb_path = join(weight_dir, path_bundle.samp_id+"_10kb_binned_frequencies.tsv")
        binned_1kb_path = join(weight_dir, path_bundle.samp_id+"_1kb_binned_frequencies.tsv")

        output_dir = weight_dir
        ws = aggregate_params.window_size_centromeres \
            if region == "centromeres" else aggregate_params.window_size_telomeres

        print(
            f"Make an aggregated of contacts around {region} ({weight_dir.split('/')[-1]}, "
            f"{'with' if is_normalized else 'no'} normalization)")

        aggregate(
            binned_10kb_contacts_path=binned_10kb_path,
            binned_1kb_contacts_path=binned_1kb_path,
            centros_coord_path=centromeres_coordinates_path,
            oligos_path=oligos_path,
            window_size=ws,
            on=region,
            output_dir=output_dir,
            exclude_probe_chr=aggregate_params.excluded_probe_chr,
            excluded_chr_list=aggregate_params.excluded_chr_list,
            additional_path=additional_groups,
            inter_normalization=is_normalized,
            plot=False
        )

    print(f"--- {path_bundle.samp_id} DONE --- \n\n")


def check_nan(str_):
    return str_ != str_


if __name__ == "__main__":
    #   Example command to enter for parameters (parse)
    """
    -s ../data/inputs/samplesheet.csv
    -f ../data/inputs/fragments_list_S288c_DSB_LY_Capture_artificial_DpnIIHinfI.txt
    -c ../data/inputs/S288c_chr_centro_coordinates.tsv 
    -o ../data/inputs/capture_oligo_positions.csv
    -a ../data/inputs/additional_probe_groups.tsv
    -b 1000 2000 3000 5000 10000 20000 40000 50000 80000 100000
    --window-size-centros 150000  
    --window-size-telos 15000
    --excluded-chr chr2 chr3 2_micron mitochondrion chr_artificial
    --exclude-probe-chr 
    """

    parser = argparse.ArgumentParser(
        description="Script that processes sshic samples data.")

    parser.add_argument('-s', '--samplesheet', type=str, required=True,
                        help='Path to the samplesheet (.csv) that contains samples and their respective references ')

    parser.add_argument('-o', '--oligos-capture', type=str, required=True,
                        help='Path to the file that contains positions of oligos')

    parser.add_argument('-f', '--fragments-list', type=str, required=True,
                        help='Path to the file fragments_list (hic_stuff output)')

    parser.add_argument('-c', '--centromeres-coordinates', type=str, required=True,
                        help='Path to the file centromeres_coordinates')

    parser.add_argument('-b', '--binning-sizes', nargs='+', type=int, required=True,
                        help='desired bin size for the rebin step')

    parser.add_argument('-a', '--additional-groups', type=str, required=False,
                        help='Path to additional groups of probes table')

    parser.add_argument('--window-size-centros', type=int, required=True,
                        help="window (in bp) that defines a focus region to aggregated centromeres")

    parser.add_argument('--window-size-telos', type=int, required=True,
                        help="window (in bp) that defines a focus region to aggregated telomeres")

    parser.add_argument('--excluded-chr', nargs='+', type=str, required=False,
                        help='list of chromosomes to excludes to prevent bias of contacts')

    parser.add_argument('--exclude-probe-chr', action='store_true', required=False,
                        help="exclude the chromosome where the probe comes from (oligo's chromosome)")

    args = parser.parse_args()

    df_samplesheet: pd.DataFrame = pd.read_csv(args.samplesheet, sep=",")
    samples = {}
    for _, row in df_samplesheet.iterrows():
        samples[row.loc["sample"]] = []
        if len(row) > 1:
            for i in range(1, len(row)):
                if not check_nan(row.iloc[i]):
                    samples[row.loc["sample"]].append(row.iloc[i])

    for samp in samples:
        refs = samples[samp]
        sample_path_bundle = PathBundle(samp, refs)
        sample_aggregate_params_centros = AggregateParams(
            args.window_size_centros, args.window_size_telos, args.exclude_probe_chr, args.excluded_chr)

        sample_data = [
            sample_path_bundle, args.oligos_capture, args.fragments_list, args.centromeres_coordinates,
            args.binning_sizes, sample_aggregate_params_centros, args.additional_groups]
        pipeline(*sample_data)
