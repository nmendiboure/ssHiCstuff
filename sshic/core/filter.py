import re
import os
import sys
import argparse
import pandas as pd
from utils import frag2


def oligos_correction(oligos_path: str):
    """
    Correct the oligos DataFrame by setting the column names to
    lowercase and sorting by chromosome and start position.

    Parameters
    ----------
    oligos_path : str
        Path to the oligos input CSV file.

    Returns
    -------
    pd.DataFrame
        The corrected oligos DataFrame.
    """
    oligos = pd.read_csv(oligos_path, sep=",")
    oligos.columns = [oligos.columns[i].lower() for i in range(len(oligos.columns))]
    oligos.sort_values(by=['chr', 'start'], inplace=True)
    oligos.reset_index(drop=True, inplace=True)

    return oligos


def fragments_correction(fragments_path: str):
    """
    Correct the fragments DataFrame by reorganizing the columns and creating a new 'frag' column.

    Parameters
    ----------
    fragments_path : str
        Path to the fragments input TXT file (generated by hicstuff).

    Returns
    -------
    pd.DataFrame
        The corrected fragments DataFrame.
    """
    fragments = pd.read_csv(fragments_path, sep='\t')
    fragments = pd.DataFrame({'frag': [k for k in range(len(fragments))],
                              'chr': fragments['chrom'],
                              'start': fragments['start_pos'],
                              'end': fragments['end_pos'],
                              'size': fragments['size'],
                              'gc_content': fragments['gc_content']
                              })
    return fragments


def starts_match(
        fragments: pd.DataFrame,
        oligos: pd.DataFrame
):
    """
    Update the start positions of the oligos DataFrame based on the corresponding fragment positions.

    If the capture oligo is inside a fragment, update the start position of the oligos DataFrame with the start
    position of the fragment.

    Parameters
    ----------
    fragments : pd.DataFrame
        The fragments DataFrame.
    oligos : pd.DataFrame
        The oligos DataFrame.

    Returns
    -------
    pd.DataFrame
        The updated oligos DataFrame.
    """
    l_starts = []
    for i in range(len(oligos)):
        oligos_chr = oligos['chr'][i]
        middle = int((oligos['end'][i] - oligos['start'][i] - 1) / 2 + oligos['start'][i] - 1)
        if oligos_chr == 'chr_artificial':
            for k in reversed(range(len(fragments))):
                interval = range(fragments['start'][k], fragments['end'][k])
                fragments_chr = fragments['chr'][k]
                if middle in interval and fragments_chr == oligos_chr:
                    l_starts.append(fragments['start'][k])
                    break
        else:
            for k in range(len(fragments)):
                interval = range(fragments['start'][k], fragments['end'][k] + 1)
                fragments_chr = fragments['chr'][k]

                if middle in interval and fragments_chr == oligos_chr:
                    l_starts.append(fragments['start'][k])
                    break
    oligos['start'] = list(l_starts)
    return oligos


def oligos_fragments_joining(
        fragments: pd.DataFrame,
        oligos: pd.DataFrame
):
    """
    Join the oligos and fragments DataFrames, removing fragments that do not contain an oligo region.

    Updates the start and end columns with the corresponding fragment positions.

    Parameters
    ----------
    fragments : pd.DataFrame
        The fragments DataFrame.
    oligos : pd.DataFrame
        The oligos DataFrame.

    Returns
    -------
    pd.DataFrame
        The joined oligos and fragments DataFrame.
    """
    oligos = starts_match(fragments, oligos)
    oligos.set_index(['chr', 'start'])
    oligos.pop("end")
    fragments.set_index(['chr', 'start'])
    oligos_fragments = fragments.merge(oligos, on=['chr', 'start'])
    oligos_fragments.sort_values(by=['chr', 'start'])
    return oligos_fragments


def contacts_correction(contacts_path: str):
    """
    Reorganize the contacts DataFrame by removing the first row, resetting the index, and renaming the columns.

    Parameters
    ----------
    contacts_path : str
        Path to the sparse_contacts input TXT file (generated by hicstuff).

    Returns
    -------
    pd.DataFrame
        The corrected contacts DataFrame.
    """
    contacts = pd.read_csv(contacts_path, sep='\t', header=None)
    contacts.drop([0], inplace=True)
    contacts.reset_index(drop=True, inplace=True)
    contacts.columns = ['frag_a', 'frag_b', 'contacts']

    return contacts


def first_join(x: str, oligos_fragments: pd.DataFrame, contacts: pd.DataFrame):
    """
    Join the contacts and oligos_fragments DataFrames, keeping only the rows that have their 'x' fragment
    (either 'frag_a' or 'frag_b', see contacts_correction function).

    Parameters
    ----------
    x : str
        Either 'a' or 'b', indicating whether to join on 'frag_a' or 'frag_b'.
    oligos_fragments : pd.DataFrame
        The joined oligos and fragments DataFrame.
    contacts : pd.DataFrame
        The corrected contacts DataFrame.

    Returns
    -------
    pd.DataFrame
        The joined contacts and oligos_fragments DataFrame.
    """

    joined = contacts.merge(oligos_fragments, left_on='frag_'+x, right_on='frag', how='inner')
    return joined


def second_join(
        x: str,
        fragments: pd.DataFrame,
        oligos_fragments: pd.DataFrame,
        contacts: pd.DataFrame
):
    """
    Add the fragments DataFrame information (=columns) for the y fragment after the first join
    (see first_join function). This is only for the y fragment, because the x fragments already have their
    information in the oligos_fragments DataFrame.

    Parameters
    ----------
    x : str
        Either 'a' or 'b', indicating which fragment corresponds to an oligo.
    fragments : pd.DataFrame
        The corrected fragments DataFrame.
    oligos_fragments : pd.DataFrame
        The joined oligos and fragments DataFrame.
    contacts : pd.DataFrame
        The corrected contacts DataFrame.

    Returns
    -------
    pd.DataFrame
        The joined DataFrame with added fragment information for the y fragment.
    """
    new_contacts = first_join(x, oligos_fragments, contacts)
    y = frag2(x)
    joined = new_contacts.join(fragments.drop("frag", axis=1),
                               on='frag_'+y,
                               lsuffix='_' + x[-1],
                               rsuffix='_' + y[-1], how='left')

    # puts a suffix to know what fragment corresponds to an oligo
    joined.rename(columns={"type": "type_" + x[-1],
                           "name": "name_" + x[-1],
                           "sequence": "sequence_" + x[-1]
                           },
                  inplace=True)
    return joined


def filter_contacts(
        oligos_path: str,
        fragments_path: str,
        contacts_path: str,
        output_dir: str
):
    """
    Filter the contacts based on the oligos and fragments data, and save the filtered contacts to a TSV file.

    Parameters
    ----------
    oligos_path : str
        Path to the oligos input CSV file.
    fragments_path : str
        Path to the fragments input TXT file (generated by hicstuff).
    contacts_path : str
        Path to the sparse_contacts input TXT file (generated by hicstuff).
    output_dir : str
        Path to the output directory.

    Returns
    -------
    None
    """
    sample_filename = contacts_path.split("/")[-1]
    sample_id = re.search(r"AD\d+[A-Z]*", sample_filename).group()
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, sample_id+'_filtered.tsv')

    fragments = fragments_correction(fragments_path)
    oligos = oligos_correction(oligos_path)
    contacts = contacts_correction(contacts_path)
    oligos_fragments = oligos_fragments_joining(fragments, oligos)
    df1 = second_join('a', fragments, oligos_fragments, contacts)
    df2 = second_join('b', fragments, oligos_fragments, contacts)

    contacts_joined = pd.concat([df1, df2])
    contacts_joined.drop("frag", axis=1, inplace=True)
    contacts_joined.sort_values(by=['frag_a', 'frag_b', 'start_a', 'start_b'], inplace=True)
    contacts_filtered = contacts_joined.convert_dtypes().reset_index(drop=True)
    contacts_filtered.to_csv(output_path, sep='\t', index=False)


def main(argv=None):
    """
    Main function to run the filter_contacts script.

    Parses command line arguments and calls the filter_contacts function.

    Parameters
    ----------
    argv : list of str, optional
        List of command line arguments, by default None.

    Returns
    -------
    None
    """

    #   Example :
    """
    -f ../test_data/AD162_classic/fragments_list.txt 
    -c ../test_data/AD162_classic/AD162/AD162_S288c_DSB_LY_Capture_artificial_cutsite_q30.txt 
    -o ../test_data/AD162_classic/AD162/
    --oligos ../test_data/AD162_classic/capture_oligo_positions.csv 
    """

    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print('Please enter arguments correctly')
        exit(0)

    parser = argparse.ArgumentParser(description='Contacts filter arguments')

    parser.add_argument('-f', '--fragments', type=str, required=True,
                        help='Path to the fragments_input.txt file (generated by hicstuff)')
    parser.add_argument('-c', '--contacts', type=str, required=True,
                        help='Path to the sparse_contacts_input.txt file (generated by hicstuff)')
    parser.add_argument('--oligos', type=str, required=True,
                        help='Path to the oligos_input.csv file')
    parser.add_argument('-o', '--output-dir', type=str, required=True,
                        help='Path to the output directory')

    args = parser.parse_args(argv)

    filter_contacts(
        args.oligos,
        args.fragments,
        args.contacts,
        args.output_dir
    )


if __name__ == "__main__":
    main(sys.argv[1:])
