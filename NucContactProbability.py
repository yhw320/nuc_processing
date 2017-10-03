"""
---- COPYRIGHT ----------------------------------------------------------------

Copyright (C) 20016-2017
Tim Stevens (MRC-LMB) and Wayne Boucher (University of Cambridge)


---- LICENSE ------------------------------------------------------------------

This file is part of NucProcess.

NucProcess is free software: you can redistribute it and/or modify it under the
terms of the GNU Lesser General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

NucProcess is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with NucProcess.  If not, see <http://www.gnu.org/licenses/>.


---- CITATION -----------------------------------------------------------------

If you are using this software for academic purposes, we suggest quoting the
following reference:

Stevens TJ, Lando D, Basu S, Atkinson LP, Cao Y, Lee SF, Leeb M, Wohlfahrt KJ,
Boucher W, O'Shaughnessy-Kirwan A, Cramard J, Faure AJ, Ralser M, Blanco E, Morey
L, Sans� M, Palayret MGS, Lehner B, Di Croce L, Wutz A, Hendrich B, Klenerman D, 
Laue ED. 3D structures of individual mammalian genomes studied by single-cell
Hi-C. Nature. 2017 Apr 6;544(7648):59-64. doi: 10.1038/nature21429. Epub 2017 Mar
13. PubMed PMID: 28289288; PubMed Central PMCID: PMC5385134.

"""

import sys
import os
import numpy as np
import NucSvg


PROG_NAME = 'nuc_contact_probability'
VERSION = '1.0.0'
DESCRIPTION = 'Chromatin contact (NCC format) probability vs sequence separation graph module for Nuc3D and NucTools'
READ_BUFFER = 2**16

COLORS = ['#0040FF','#FF0000','#B0B000','#808080']

def info(msg, prefix='INFO'):

  print('%8s : %s' % (prefix, msg))


def warn(msg, prefix='WARNING'):

  print('%8s : %s' % (prefix, msg))


def fatal(msg, prefix='%s FAILURE' % PROG_NAME):

  print('%8s : %s' % (prefix, msg))
  sys.exit(0)
  
  
def plot_contact_probability_seq_sep(ncc_paths, svg_path, bin_size=100, svg_width=800, labels=None):
 
  bin_size *= 1e3
  
  from matplotlib import pyplot as plt
  
  f, ax = plt.subplots()
  
  ax.set_alpha(0.5)
  ax.set_title('Contact sequence separations')
  
  x_limit = 10.0 ** 7.7 # log_max
  
  multi_set = len(ncc_paths) > 1
  
  for g, ncc_group in enumerate(ncc_paths):
    chromo_limits = {}
    contacts = {}
    seq_seps_all = []
    seq_seps = {}
    weights_all = []
    weights = {}
    
    n_files = len(ncc_group)
    
    for n, ncc_path in enumerate(ncc_group):
      print g, n
      seq_seps[ncc_path] = []
      weights[ncc_path] = []
 
      # Load cis NCC data
      with open(ncc_path, 'r', READ_BUFFER) as in_file_obj:
        for line in in_file_obj:
          chr_a, f_start_a, f_end_a, start_a, end_a, strand_a, chr_b, f_start_b, f_end_b, start_b, end_b, strand_b, ambig_group, pair_id, swap_pair = line.split()
 
          if chr_a != chr_b:
            continue
 
          f_start_a = int(f_start_a)
          f_end_a = int(f_end_a)
          start_a = int(start_a)
          end_a = int(end_a)
          f_start_b = int(f_start_b)
          f_end_b = int(f_end_b)
          start_b = int(start_b)
          end_b  = int(end_b)
 
          if chr_a in chromo_limits:
            s, e = chromo_limits[chr_a]
            chromo_limits[chr_a] = (min(s, f_start_a, f_start_b), max(e, f_end_a, f_end_b))
          else:
            chromo_limits[chr_a] = (min(f_start_a, f_start_b), max(f_end_a, f_end_b))
 
          if chr_a in contacts:
            contact_list = contacts[chr_a]
 
          else:
            contact_list = []
            contacts[chr_a] = contact_list
 
          if strand_a > 0:
            p_a = f_end_a
          else:
            p_a = f_start_a
 
          if strand_b > 0:
            p_b = f_end_b
          else:
            p_b = f_start_b
 
          contact_list.append((p_a, p_b))

      for chromo in contacts:
 
        contact_array = np.array(contacts[chromo], np.int32)
 
        seps = abs(contact_array[:,0]-contact_array[:,1])

        indices = seps.nonzero()
        seps    = seps[indices]
 
        p_start, p_end = chromo_limits[chromo]
        size = float(p_end-p_start+1)
 
        prob = (size/(size-seps)).tolist() # From fraction of chromosome that could give rise to each separation
        seps = seps.tolist()
        
        if not multi_set:
          seq_seps[ncc_path] += seps
          weights[ncc_path] += prob
        
        seq_seps_all += seps
        weights_all += prob


    seq_seps_all = np.array(seq_seps_all)
 
    log_max  = (int(2 * np.log10(seq_seps_all.max()))/2.0)
    log_min  = np.log10(bin_size)
 
    num_bins = (x_limit-bin_size)/bin_size
    bins = np.linspace(bin_size, x_limit, num_bins)
 
    opacities = []
    data_lists = []
    colors = []
    names = []
 
    comb_y_data = None
 
    if not multi_set and (n_files > 1):
      for i, ncc_path in enumerate(seq_seps.keys()):
        data = np.array(seq_seps[ncc_path])

        hist, edges = np.histogram(data, bins=bins, weights=weights[ncc_path], normed=True)
 
        if comb_y_data is None:
          comb_y_data = np.zeros((n_files,len(hist)))
 
        idx = hist.nonzero()
        hist = hist[idx]
        comb_y_data[i,idx] = hist
          
    hist, edges = np.histogram(seq_seps_all, bins=bins, weights=weights_all, normed=True)
    idx = hist.nonzero()
 
    hist = hist[idx]
    edges = edges[idx]
 
    x_data = np.log10(edges)
    y_data = np.log10(hist)
    
    if not multi_set:
      y_err = comb_y_data.std(axis=0, ddof=1)[idx]
      y_lower = y_data - np.log10(hist-y_err)
      y_upper = np.log10(hist+y_err) - y_data
 
    y_min = int(2.0 * y_data.min())/2.0
    y_max = int(1.0 + 2.0 * y_data.max())/2.0
    
    if labels:
      label = labels.pop(0).replace('_', ' ')
    
    elif n_files > 1:
      if len(ncc_paths) > 1:
        label = 'Group %d' % (g+1)
      else:
        label = 'Combined datasets'
 
    else:
      label = None
 
    """
    data_lists.append(zip(x_data, y_data))
    colors.append('#000000')
    names.append(label)
    opacities.append(1.0)
 
    x1 = x_data[2]
    y1 = y_data[2]
    dy = 0.25

    data_lists.append([(x1, y1+dy), (x1+1.5, y1+dy-1.50)])
    colors.append('#808080')
    names.append(None)
    opacities.append(0.5)
 
    data_lists.append([(x1, y1-dy), (x1+1.5, y1-dy-2.25)])
    colors.append('#808080')
    names.append(None)
    opacities.append(0.5)

    x_range = np.arange(np.log10(bin_size), np.log10(x_limit), 0.5)
    y_range = np.arange(y_min, y_max, 0.5)

    svg_doc = NucSvg.SvgDocument()
 
    pad = 100
    width   = svg_width - pad
    height  = svg_width - pad
    x_label = 'Sequence separation (bp)'
    y_label = 'Contact probability (%d kb bins)' % (bin_size/1000)
    title   = 'Contact sequence separations'
    texts = [(u'\u03bb=1.0', '#808080', (x1+1.5, y1+dy-1.50)),
             (u'\u03bb=1.5', '#808080', (x1+1.5, y1-dy-2.25))]
 
    svg_doc.graph(0, 0, width, height, data_lists, x_label, y_label,
              names=names, colors=colors,  graph_type=NucSvg.LINE_TYPE,
              symbols=None, line_widths=None, symbol_sizes=None,
              legend=(6.4, -6.0),
              title=title, x_labels=None, plot_offset=(pad, pad),
              axis_color='black', bg_color='#F0F0F0', font=None, font_size=16, line_width=1,
              x_ticks=True, y_ticks=True, x_grid=False, y_grid=False,
              texts=texts, opacities=opacities,
              x_log_base='10', y_log_base='10')
 
    if svg_path == '-':
      print(svg_doc.svg(svg_width, svg_width))
 
    elif svg_path:
      svg_doc.write_file(svg_path, svg_width, svg_width)

    else:
      return svg_doc.svg(svg_width, svg_width)
    """
 
    if multi_set:
      ax.plot(x_data, y_data, label=label, color=COLORS[g], linewidth=1, alpha=0.5)
    
    else:
      ax.fill_between(x_data, y_data-y_lower, y_data+y_upper, color='#FF0000', alpha=0.5, linewidth=0.5)
      ax.plot(x_data, y_data, label=label, color='#000000', alpha=1.0)
      ax.plot([],[], linewidth=8, color='#FF0000', alpha=0.5, label='$\pm\sigma$ over datasets')
 
  x_range = np.arange(np.log10(bin_size), np.log10(x_limit), 0.5)
  
  ax.set_xlabel('Sequence separation (bp)')
  ax.set_ylabel('Contact probability (100 kb bins)')
  ax.xaxis.set_ticks(x_range)
  ax.set_xticklabels(['$10^{%.1f}$' % x for x in x_range], fontsize=12)
  ax.set_xlim((np.log10(bin_size), np.log10(x_limit)))
  
  y_min, y_max = -9.5, -5.5
  y_range = np.arange(y_min, y_max, 0.5)
  ax.yaxis.set_ticks(y_range)
  ax.set_yticklabels(['$10^{%.1f}$' % x for x in y_range], fontsize=12)
  ax.set_ylim((y_min, y_max))
 
  ax.plot([5.5, 7.0], [-6.0, -7.50], color='#808080', alpha=0.5, linestyle='--')
  ax.plot([5.5, 7.0], [-6.5, -8.75], color='#808080', alpha=0.5, linestyle='--')
  ax.text(7.0, -7.50, '$\lambda=1.0$', color='#808080', verticalalignment='center', alpha=0.5, fontsize=14)
  ax.text(7.0, -8.75, '$\lambda=1.5$', color='#808080', verticalalignment='center', alpha=0.5, fontsize=14)
  
  ax.legend()
  
  plt.savefig(svg_path)
  plt.show()
    
# python NucContactProbability.py -i /data/hi-c/GSE80280_stevens/*.ncc -o test.svg -l Stevens_[8] Nagano_[20] Flyamer_[20] Ramani_[500] -i2 /data/hi-c/GSE94489_nagano/*.ncc -i3 /data/hi-c/GSE80006_flyamer/*.ncc -i4 ncc_temp/*.ncc  


if __name__ == '__main__':
 
  from argparse import ArgumentParser
  
  epilog = 'For further help email tjs23@cam.ac.uk or wb104@cam.ac.uk'
  
  arg_parse = ArgumentParser(prog=PROG_NAME, description=DESCRIPTION,
                             epilog=epilog, prefix_chars='-', add_help=True)

  arg_parse.add_argument('-i', metavar='NCC_FILES', nargs='+',
                         help='Input NCC format chromatin contact file(s). Wildcards accepted')
                         
  arg_parse.add_argument('-o', metavar='SVG_FILE',
                         help='Output SVF format file. Use "-" to print SVG to stdout rather than make a file.')

  arg_parse.add_argument('-i2', metavar='NCC_FILES', nargs='*',
                         help='Second group of input NCC format chromatin contact file(s). Wildcards accepted')

  arg_parse.add_argument('-i3', metavar='NCC_FILES', nargs='*',
                         help='Third group of input NCC format chromatin contact file(s). Wildcards accepted')
                         
  arg_parse.add_argument('-i4', metavar='NCC_FILES', nargs='*',
                         help='Fourth group of input NCC format chromatin contact file(s). Wildcards accepted')

  arg_parse.add_argument('-l', metavar='LABELS', nargs='*',
                         help='Text labels for groups of input files')

  arg_parse.add_argument('-w', default=800, metavar='SVG_WIDTH', type=int,
                         help='SVG document width')

  arg_parse.add_argument('-s', default=100, metavar='KB_BIN_SIZE', type=int,
                         help='Sequence region size in kilobases for calculation of contact probabilities. Default is 100 (kb)')

  args = vars(arg_parse.parse_args())
  
  ncc_paths1 = args['i']
  ncc_paths2 = args['i2'] or None
  ncc_paths3 = args['i3'] or None
  ncc_paths4 = args['i4'] or None
  svg_path   = args['o']
  svg_width  = args['w']
  bin_size   = args['s']
  labels     = args['l'] or None
  
  ncc_paths = [x for x in (ncc_paths1, ncc_paths2, ncc_paths3, ncc_paths4) if x]
  
  if not ncc_paths:
    import sys
    arg_parse.print_help()
    fatal('No input NCC format files specified') 

  for group in ncc_paths:
    for ncc_path in group:
      if not os.path.exists(ncc_path):
        fatal('NCC file could not be found at "{}"'.format(ncc_path))  
  
  if not svg_path:
    arg_parse.print_help()
    fatal('Output SVG file path not specified') 
  
  dir_name, file_name = os.path.split(svg_path)
  
  if dir_name and not os.path.exists(dir_name):
    fatal('Directory "%s" for output could not be found') 
  
  if not file_name.lower().endswith('.svg'):
    if svg_path != '-':
      svg_path = svg_path + '.svg'
  
  
  plot_contact_probability_seq_sep(ncc_paths, svg_path, bin_size, svg_width, labels)
