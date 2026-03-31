# Tooling Context

## AI Tools

### Cowork (Claude Desktop App)
- **When to use**: Research, paper reading, web search, file creation, planning, writing
- **Strengths**: Web access, Zotero MCP, PubMed MCP, document creation (docx/pptx/xlsx), skills system
- **Limitation**: Cannot SSH to Longleaf; cannot run simulations
- **State file**: Reads CLAUDE.md from project folder on startup

### Claude Code Terminal
- **When to use**: SSH to Longleaf, install software, write scripts, submit Slurm jobs, debug HPC issues
- **Strengths**: Direct terminal access, can run commands on Longleaf via SSH
- **Limitation**: No web search, no Zotero, limited document creation
- **State file**: Also reads CLAUDE.md from project folder

### Sync Protocol
Both tools read the same `CLAUDE.md` in the project root. When either tool makes progress:
1. Update the "Project Status" table in CLAUDE.md
2. This way the other tool picks up the latest state next session

## HPC Environment (UNC Longleaf)

### Storage
| Path | Quota | Use |
|------|-------|-----|
| /nas/longleaf/home/liualex | 50 GB (near full!) | Config files only |
| /work/users/l/i/liualex | 10 TB | Conda envs, simulation data |

### Software
| Software | How to load |
|----------|------------|
| AMBER 24p3 | `module load amber/24p3` (GPU only: pmemd.cuda) |
| PLUMED 2.9 | `conda activate trpb-md` (env on /work) |
| GROMACS | **Not yet installed** — need to install with PLUMED2 patch |

### PLUMED Runtime
```bash
export PLUMED_KERNEL=/work/users/l/i/liualex/conda/envs/trpb-md/lib/libplumedKernel.so
```
