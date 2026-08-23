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
# activate the project environment in every interactive shell.
#
# Both lines are required; keep or drop them together.
#
#  - `conda init` writes the "conda initialize" block that defines the shell
#    function. Without it `conda activate` is not a command at all, so the
#    activation below fails and, more importantly, so does the one VS Code's
#    Python Environments extension types into its terminals: because this
#    block sets CONDA_SHLVL, that extension takes its "already sourced" path
#    and emits a bare `conda activate <env>` with no `source` in front of it.
#  - The explicit activation is what VS Code-independent shells rely on
#    (`docker exec`, CI, ssh); conda's auto_activate would land them in base.
#
# The interpreter VS Code itself uses is a separate matter: the Python
# Environments extension ignores python.defaultInterpreterPath and stores its
# per-project environment in VS Code's internal DB, so it has to be picked once
# via "Python: Select Interpreter". See .devcontainer/devcontainer.json.
RUN conda init bash zsh \
    && printf '\n# Auto-activate the project conda environment\nconda activate %s 2>/dev/null || true\n' "${CONDA_ENV_NAME}" \
        | tee -a /home/vscode/.bashrc /home/vscode/.zshrc > /dev/null

# uv (fast pip alternative)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/vscode/.local/bin:${PATH}"

# プロジェクトの conda 環境をここで作り込む。数分かかる処理なので、コンテナ
# 再作成のたびに走る postCreateCommand ではなくイメージ側に置いている。
#
# COPY するのは environment.yml だけにすること。ソースごと COPY すると、
# 無関係な .py を 1 行直しただけで COPY 以降のレイヤーキャッシュが無効になり、
# 直後の env create がまるごとやり直しになる。
#
# 自分自身の editable install (-e .) をここに含めないのも同じ理由。あれは
# setuptools_scm のために .git を必要とし、.git を COPY するとコミットする
# たびにキャッシュが飛ぶ。editable install は postCreateCommand 側に残してある。
# 環境名は environment.yml の name と CONDA_ENV_NAME で揃えてある。
COPY --chown=vscode:vscode environment.yml /tmp/environment.yml
RUN mamba env create -y -f /tmp/environment.yml \
    && mamba clean -yaf \
    && rm /tmp/environment.yml

WORKDIR /workspaces/python-template
