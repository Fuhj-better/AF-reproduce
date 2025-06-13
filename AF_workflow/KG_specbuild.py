import asyncio
from pathlib import Path
from pprint import pprint

import pandas as pd
import os

import graphrag.api as api
from graphrag.config.load_config import load_config
from graphrag.index.typing.pipeline_run_result import PipelineRunResult

# Define project directory
ROOT_DIRECTORY = "svtest2"

PROJECT_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../','svtest2')


async def build_index():
    """
    Main asynchronous function to execute GraphRag's index building and global search operations.
    """
    print("Loading GraphRag configuration...")
    # Load GraphRag configuration
    graphrag_config = load_config(Path(PROJECT_DIRECTORY))
    print("Configuration loaded.")

    print("\nBuilding index...")
    # Build index, this is an asynchronous operation
    index_result: list[PipelineRunResult] = await api.build_index(config=graphrag_config)

    # Print index building results
    for workflow_result in index_result:
        status = f"error\n{workflow_result.errors}" if workflow_result.errors else "success"
        print(f"Workflow Name: {workflow_result.workflow}\tStatus: {status}")
    print("Index building complete.")

async def global_research(query,response_type="Multiple Paragraphs"):
    graphrag_config = load_config(Path(PROJECT_DIRECTORY))
    print("Configuration loaded.")

    print("\nLoading entities, communities, and community reports...")
    # Load data from parquet files
    # Please ensure that the 'output' directory and corresponding parquet files exist
    # before running this script. These files are usually generated after a successful index build.
    try:
        entities = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/entities.parquet")
        communities = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/communities.parquet")
        community_reports = pd.read_parquet(
            f"{PROJECT_DIRECTORY}/output/community_reports.parquet"
        )
        print("Data loaded successfully.")
    except FileNotFoundError as e:
        print(f"Error: Could not load Parquet files. Please ensure the index has been built successfully and the files exist. Error message: {e}")
        return # Stop execution if files are not found

    print(f"\nExecuting global search query: '{query}'...")
    # Execute global search, this is an asynchronous operation
    response, context = await api.global_search(
        config=graphrag_config,
        entities=entities,
        communities=communities,
        community_reports=community_reports,
        community_level=2,
        dynamic_community_selection=False,
        response_type=response_type,
        query=query,
    )
    print("Global search complete.")

    # print("\nSearch Response:")
    # # Print search response
    # print(response)
    return response,context


