FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        curl \
        ca-certificates \
        build-essential \
        zsh \
        tmux \
    && rm -rf /var/lib/apt/lists/*

# Node.js LTS (for Claude Code)
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Miniforge (mamba included)
ENV MAMBA_ROOT_PREFIX=/opt/conda
RUN ARCH="$(uname -m)" \
    && curl -fsSL "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-${ARCH}.sh" \
        -o /tmp/miniforge.sh \
    && bash /tmp/miniforge.sh -b -p "${MAMBA_ROOT_PREFIX}" \
    && rm /tmp/miniforge.sh \
    && "${MAMBA_ROOT_PREFIX}/bin/mamba" clean --all --yes \
    && chown -R vscode:vscode "${MAMBA_ROOT_PREFIX}"

ENV PATH="${MAMBA_ROOT_PREFIX}/bin:${PATH}"

# Verify mamba is available
RUN mamba --version

# Claude Code (global npm install)
RUN npm install -g @anthropic-ai/claude-code

# Switch to non-root user
USER vscode

# Keep Claude Code's config file inside the volume-backed directory. By default it
# lives at ~/.claude.json, outside ~/.claude, and would be lost on every rebuild.
ENV CLAUDE_CONFIG_DIR=/home/vscode/.claude

# Project conda environment (keep in sync with environment.yml)
ENV CONDA_ENV_NAME=work

# Register the conda shell hook so `conda activate` works in bash/zsh, and
# activate the project environment in every interactive shell. This is what
# makes VS Code terminals start inside the environment; python.defaultInterpreterPath
# alone only tells the Python extension which interpreter to prefer.
RUN conda init bash zsh \
    && printf '\n# Auto-activate the project conda environment\nconda activate %s 2>/dev/null || true\n' "${CONDA_ENV_NAME}" \
        | tee -a /home/vscode/.bashrc /home/vscode/.zshrc > /dev/null

# uv (fast pip alternative)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/vscode/.local/bin:${PATH}"

WORKDIR /workspaces/python-template
