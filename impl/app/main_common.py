"""
This module is for ad-hoc tasks not related to the actual working app.
Usage:
    python main_common.py log_defined_env_vars
    python main_common.py gen_ps1_env_var_script
    python main_common.py gen_bicep_params_files
    python main_common.py gen_environment_variables_md
    python main_common.py gen_all
    python main_common.py owl_visualizer ontologies/libraries.owl
Options:
  -h --help     Show this screen.
  --version     Show version.
"""

import logging
import os
import sys
import textwrap
import time

from docopt import docopt
from dotenv import load_dotenv

from src.services.config_service import ConfigService
from src.services.cosmos_vcore_service import CosmosVCoreService
from src.services.logging_level_service import LoggingLevelService
from src.util.fs import FS
from src.util.owl_visualizer import OwlVisualizer
from src.util.template import Template

logging.basicConfig(
    format="%(asctime)s - %(message)s", level=LoggingLevelService.get_level()
)


def print_options(msg):
    print(msg)
    arguments = docopt(__doc__, version="1.0.0")
    print(arguments)


def explore_logging():
    logging.info("explore_logging")
    opts = dict()
    opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
    logging.info("opts: {}".format(opts))
    vcore = CosmosVCoreService(opts)

    try:
        1 / 0
    except Exception as e:
        # python logging.exception(e, stack_info=True, exc_info=True)
        logging.exception(e, stack_info=True, exc_info=True)


def log_defined_env_vars():
    logging.info("log_defined_env_vars")
    ConfigService.log_defined_env_vars()


def gen_ps1_env_var_script():
    env_var_names = sorted(ConfigService.defined_environment_variables().keys())
    samples = ConfigService.sample_environment_variable_values()
    lines = list()
    lines.append(
        "# PowerShell script to set the necessary CAIG_ environment variables,"
    )
    lines.append("# generated by main.py on {}".format(time.ctime()))
    lines.append("# Edit ALL of these generated values per your actual deployment.")
    lines.append("")
    lines.append('echo "Setting CAIG environment variables"')

    for name in env_var_names:
        value = "xxx"  # ConfigService.envvar(name, '')
        if name in samples:
            value = samples[name]
        lines.append("")
        lines.append("echo 'setting {}'".format(name))
        lines.append(
            "[Environment]::SetEnvironmentVariable(|{}|, |{}|, |User|)".format(
                name, value
            ).replace("|", '"')
        )
    lines.append("")
    FS.write_lines(lines, "../set-caig-env-vars-sample.ps1")


def gen_bicep_params_files():
    bicep_parm_names_lines = list()
    bicep_bicepparam_lines = list()
    bicep_parm_names_lines.append(
        "// Bicep parameter names generated by main.py on {}".format(time.ctime())
    )
    bicep_parm_names_lines.append("// Include these to the top of your caig.bicep file")
    bicep_parm_names_lines.append("")

    bicep_bicepparam_lines.append(
        "// Bicep bicepparam entries generated by main.py on {}".format(time.ctime())
    )
    bicep_bicepparam_lines.append("// Include these in your caig.bicepparam file")
    bicep_bicepparam_lines.append("")
    bicep_bicepparam_lines.append("using './caig.bicep'")
    bicep_bicepparam_lines.append("")

    env_var_names = sorted(ConfigService.defined_environment_variables().keys())
    excluded_var_names = excluded_bicep_envvars()

    for name in env_var_names:
        if name in excluded_var_names:
            pass
        else:
            bicepName = camel_case(name)
            value = ConfigService.envvar(name, "")

            # declare the param in the bicep file
            bicep_parm_names_lines.append("param {} string".format(bicepName))

            # get the param value in the bicepparam file
            bicepparam_line = "param {} = readEnvironmentVariable('{}')".format(
                bicepName, name
            )
            bicep_bicepparam_lines.append(bicepparam_line)

    bicep_parm_names_lines.append("")
    bicep_bicepparam_lines.append("")

    FS.write_lines(bicep_parm_names_lines, "../deployment/generated-param-names.bicep")
    FS.write_lines(bicep_bicepparam_lines, "../deployment/generated.bicepparam")


def excluded_bicep_envvars():
    """
    Return a list of the CAIG_xxx environment variable names that should be excluded
    from generating the Bicep names and parameters files.  These names are used
    elsewhere in the system, but not by the Bicep deployment process.
    """
    vars = list()
    vars.append("CAIG_GRAPH_SERVICE_PORT")
    vars.append("CAIG_GRAPH_SERVICE_URL")
    vars.append("CAIG_HOME")
    vars.append("CAIG_LOG_LEVEL")
    vars.append("CAIG_USE_ALT_SPARQL_CONSOLE")
    vars.append("CAIG_WEB_APP_PORT")
    vars.append("CAIG_WEB_APP_URL")
    return vars


def gen_envvars_master_entries():
    """generate a partial config file for my personal envvar solution - cj"""
    samples = ConfigService.sample_environment_variable_values()
    env_var_names = sorted(ConfigService.defined_environment_variables().keys())
    lines = list()
    for name in env_var_names:
        value = ConfigService.envvar(name, "")
        if len(value) == 0:
            if name in samples.keys():
                value = samples[name]
        padded = name.ljust(35)
        lines.append("{} ||| {}".format(padded, value))
    FS.write_lines(lines, "tmp/caig-envvars-master.txt")


def camel_case(env_var_name):
    tokens = env_var_name.split("_")
    words = list()
    for token_idx, token in enumerate(tokens):
        if token_idx > 0:
            lcword = token.lower()
            if token_idx == 1:
                words.append(lcword)
            else:
                words.append(lcword.capitalize())
    return "".join(words)


def gen_environment_variables_md():
    lines = list()
    lines.append("# CosmosAIGraph Implementation 1 : Environment Variables")
    lines.append("")
    lines.append(
        "Per the [Twelve-Factor App methodology](https://12factor.net/config),"
    )
    lines.append("configuration is stored in environment variables.  ")
    lines.append(
        "This is the standard practice for Docker-containerized applications deployed to orchestrators"
    )
    lines.append(
        "such as Azure Kubernetes Service (AKS) and Azure Container Apps (ACA)."
    )
    lines.append("")

    lines.append("## Defined Variables")
    lines.append("")
    lines.append(
        "This reference implementation uses the following environment variables."
    )
    lines.append("Some are used at runtime in ACA, some are used for Bicep-deployment,")
    lines.append("and some are used for local workstation development.")
    lines.append("All of these begin with the prefix `CAIG_`.")
    lines.append("")

    lines.append("| Name | Description |")
    lines.append(
        "| --------------------------------- | --------------------------------- |"
    )
    env_var_names = sorted(ConfigService.defined_environment_variables().keys())
    for name in env_var_names:
        desc = ConfigService.defined_environment_variables()[name]
        lines.append("| {} | {} |".format(name, desc))

    lines.append("")
    lines.append("## Setting these Environment Variables")
    lines.append("")
    lines.append(
        "The repo contains generated PowerShell script **impl/set-caig-env-vars-sample.ps1**"
    )
    lines.append("which sets all of these CAIG_ environment values.")
    lines.append(
        "You may find it useful to edit and execute this script rather than set them manually on your system"
    )
    lines.append("")

    lines.append("")
    lines.append("## python-dotenv")
    lines.append("")
    lines.append(
        "The [python-dotenv](https://pypi.org/project/python-dotenv/) library is used"
    )
    lines.append("in each subapplication of this implementation.")
    lines.append(
        "It allows you to define environment variables in a file named **`.env`**"
    )
    lines.append(
        "and thus can make it easier to use this project during local development."
    )
    lines.append("")
    lines.append(
        "Please see the **dotenv_example** files in each subapplication for examples."
    )
    lines.append("")
    lines.append(
        "It is important for you to have a **.gitignore** entry for the **.env** file"
    )
    lines.append(
        "so that application secrets don't get leaked into your source control system."
    )
    lines.append("")

    FS.write_lines(lines, "../docs/environment_variables.md")


def gen_all():
    gen_envvars_master_entries()
    gen_ps1_env_var_script()
    gen_bicep_params_files()
    gen_environment_variables_md()


def owl_visualizer(infile):
    owl_viz = OwlVisualizer(infile)
    t = Template.get_template(os.getcwd(), "owl_viz_html_page.txt")
    html = Template.render(t, owl_viz.get_visjs_data())
    FS.write("tmp/graph.html", html)

    t = Template.get_template(os.getcwd(), "owl_viz_cytoscape_html_page.txt")
    html = Template.render(t, owl_viz.get_cytoscape_data())
    FS.write("tmp/cytoscape_graph.html", html)


def ad_hoc_development():
    logging.info("ad_hoc_development")
    content = "Flask is a simple framework for building complex web applications. It is available on PyPI as version 3.0.2. This lightweight WSGI web application framework is designed for quick and easy startups, with the scalability needed for more complex applications. Released on February 3, 2024, Flask supports Python versions 3.8 and above. It is maintained by the Pallets project and is licensed under the BSD License. Flask is known for its flexibility, allowing developers to choose their tools and libraries without enforcing any dependencies or project layout. The framework encourages community contributions and provides extensive documentation, issue tracking, and a chat platform for support. Installation can be easily done using pip. Flask also emphasizes the importance of JavaScript for full functionality in web applications."
    wrapped = textwrap.wrap(content, width=70)
    print("content: {}".format(content))
    print("wrapped: {}".format(wrapped))


if __name__ == "__main__":
    load_dotenv(override=True)

    if len(sys.argv) < 2:
        print_options("Error: invalid command-line")
        exit(1)
    else:
        try:
            func = sys.argv[1].lower()
            if func == "log_defined_env_vars":
                log_defined_env_vars()
            elif func == "gen_ps1_env_var_script":
                gen_ps1_env_var_script()
            elif func == "gen_bicep_params_files":
                gen_bicep_params_files()
            elif func == "gen_environment_variables_md":
                gen_environment_variables_md()
            elif func == "gen_all":
                gen_all()
            elif func == "owl_visualizer":
                infile = sys.argv[2]
                owl_visualizer(infile)
            elif func == "ad_hoc":
                ad_hoc_development()
            else:
                print_options("Error: invalid function: {}".format(func))
        except Exception as e:
            logging.critical(str(e))
            logging.exception(e, stack_info=True, exc_info=True)
