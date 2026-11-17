"""Reproduce the figure from unlabelled, independently sorted group values.

No cross-program subject linkage or source clinical identifiers are supplied.
These values reproduce the plot, not upstream transcript quantification.
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'trial_figure_data.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,2,figsize=(11.6,5.5),sharey=True)
for ax,panel in zip(axes.flat,data['panels']):
    for i,(key,label,color) in enumerate([('nonbenefit','No clinical benefit\n(n = 23)','#778896'),('benefit','Clinical benefit\n(n = 5)','#14657A')]):
        vals=np.array(panel[key]); jitter=np.linspace(-.13,.13,len(vals))
        ax.scatter(i+jitter,vals,s=26,color=color,alpha=.85,zorder=3,edgecolors='white',linewidths=.35)
        ax.plot([i-.2,i+.2],[np.median(vals)]*2,color='black',lw=1.9,zorder=4)
    ax.set_title(panel['label'],loc='left',fontsize=12,fontweight='bold',pad=10)
    ax.set_xticks([0,1],['No clinical benefit\n(n = 23)','Clinical benefit\n(n = 5)'])
    ax.set_xlim(-.5,1.5);ax.set_ylim(0,100);ax.set_yticks([0,25,50,75,100]);ax.grid(axis='y',color='#E4E8EB',lw=.7);ax.set_axisbelow(True)
    ax.text(.99,.98,'P = '+panel['p']+'   q = 0.521',transform=ax.transAxes,ha='right',va='top',fontsize=10)
for ax in axes[:,0]:ax.set_ylabel('Mean within-sample gene rank')
fig.subplots_adjust(left=.07,right=.99,top=.91,bottom=.09,hspace=.65,wspace=.20)
out=ROOT/'figures/baseline_pathway_outcomes.png';out.parent.mkdir(exist_ok=True);fig.savefig(out,dpi=200,facecolor='white');plt.close(fig)
print(out)
