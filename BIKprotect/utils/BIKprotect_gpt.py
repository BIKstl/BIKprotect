# an automated penetration testing parser empowered by GPT
import json
import os
import sys
import textwrap
import time
import traceback

import loguru
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import confirm
from rich.console import Console
from rich.spinner import Spinner

from BIKprotect.config.chat_config import ChatGPTConfig
from BIKprotect.prompts.prompt_class import BIKprotectPrompt
from BIKprotect.utils.APIs.module_import import dynamic_import
from BIKprotect.utils.chatgpt import ChatGPT
from BIKprotect.utils.prompt_select import prompt_ask, prompt_select
from BIKprotect.utils.task_handler import (
    local_task_entry,
    localTaskCompleter,
    main_task_entry,
    mainTaskCompleter,
)
from BIKprotect.utils.web_parser import google_search

logger = loguru.logger


def prompt_continuation(width, line_number, wrap_count):
    """
    The continuation: display line numbers and '->' before soft wraps.
    Notice that we can return any kind of formatted text from here.
    The prompt continuation doesn't have to be the same width as the prompt
    which is displayed before the first line, but in this example we choose to
    align them. The `width` input that we receive here represents the width of
    the prompt.
    """
    if wrap_count > 0:
        return " " * (width - 3) + "-> "
    text = ("- %i - " % (line_number + 1)).rjust(width)
    return HTML("<strong>%s</strong>") % text


class BIKprotect:
    postfix_options = {
        "tool": "The input content is from a security testing tool. You need to list down all the points that are interesting to you; you should summarize it as if you are reporting to a senior penetration tester for further guidance.\n",
        "user-comments": "The input content is from user comments.\n",
        "web": "The input content is from web pages. You need to summarize the readable-contents, and list down all the points that can be interesting for penetration testing.\n",
        "default": "The user did not specify the input source. You need to summarize based on the contents.\n",
    }

    options_desc = {
        "tool": " Paste the output of the security test tool used",
        "user-comments": "",
        "web": " Paste the relevant content of a web page",
        "default": " Write whatever you want, the tool will handle it",
    }

    def __init__(
        self,
        log_dir="logs",
        reasoning_model="gpt-4-turbo",
        parsing_model="gpt-4-turbo",
        useAPI=True,
        azure=False,
        use_langfuse_logging=False,
    ):
        self.log_dir = log_dir
        logger.add(sink=os.path.join(log_dir, "BIKprotect.log"))
        self.save_dir = "test_history"
        self.task_log = (
            {}
        )  # the information that can be saved to continue in the next session
        self.useAPI = useAPI
        self.parsing_char_window = 16000  # the chunk size for parsing in # of chars
        # TODO: link the parsing_char_window to the model used
        # load the module
        reasoning_model_object = dynamic_import(
            reasoning_model, self.log_dir, use_langfuse_logging=use_langfuse_logging
        )
        generation_model_object = dynamic_import(
            reasoning_model, self.log_dir, use_langfuse_logging=use_langfuse_logging
        )
        parsing_model_object = dynamic_import(
            parsing_model, self.log_dir, use_langfuse_logging=use_langfuse_logging
        )
        if useAPI is False:  # deprecated usage of cookie
            self.parsingAgent = ChatGPT(ChatGPTConfig(log_dir=self.log_dir))
            self.reasoningAgent = ChatGPT(
                ChatGPTConfig(model=reasoning_model, log_dir=self.log_dir)
            )
        else:
            self.parsingAgent = parsing_model_object
            self.generationAgent = generation_model_object
            self.reasoningAgent = reasoning_model_object
        self.prompts = BIKprotectPrompt
        self.console = Console()
        self.spinner = Spinner("line", "Processing")
        self.test_generation_session_id = None
        self.test_reasoning_session_id = None
        self.input_parsing_session_id = None
        self.chat_count = 0
        self.step_reasoning = (
            None  # the response from the reasoning session for the current step
        )
        self.history = {
            "user": [],
            "BIKprotect": [],
            "reasoning": [],
            "input_parsing": [],
            "generation": [],
            "exception": [],
        }  # the history of the current conversation

        # print the initialization message on the current implementation.
        self.console.print(
            "Welcome to BIKprotect, an automated penetration testing parser empowered by GPT.",
            style="bold green",
        )
        self.console.print("The settings are: ")
        self.console.print(
            f" - parsing model: {parsing_model_object.name}", style="bold green"
        )
        self.console.print(
            f" - reasoning model: {reasoning_model_object.name}", style="bold green"
        )
        self.console.print(f" - use API: {useAPI}", style="bold green")
        self.console.print(f" - log directory: {log_dir}", style="bold green")

    def log_conversation(self, source, text):
        """
        append the conversation into the history

        Parameters:
        ----------
        source: str
            the source of the conversation
        text: str
            the content of the conversation
        """
        # append the conversation into the history
        timestamp = time.time()
        if source not in self.history.keys():
            # an exception
            source = "exception"
        self.history[source].append((timestamp, text))

    def refresh_session(self):
        if self.useAPI:
            self.console.print(
                "You're using API mode, so no need to refresh the session."
            )
            self.log_conversation(
                "BIKprotect",
                "You're using API mode, so no need to refresh the session.",
            )
        else:
            self.console.print(
                "Please ensure that you put the curl command into `config/chatgpt_config_curl.txt`",
                style="bold green",
            )
            self.log_conversation(
                "BIKprotect",
                "Please ensure that you put the curl command into `config/chatgpt_config_curl.txt`",
            )
            input("Press Enter to continue...")
            self.parsingAgent.refresh()
            self.reasoningAgent.refresh()
            self.console.print(
                "Session refreshed. If you receive the same session refresh request, please refresh the ChatGPT page and paste the new curl request again.",
                style="bold green",
            )
            self.log_conversation("BIKprotect", "Session refreshed.")
            return "Session refreshed."

    def _feed_init_prompts(self):
        # 1. User firstly provide basic information of the task
        init_description = prompt_ask(
            "Please describe the penetration testing task in one line, including the target IP, task type, etc.\n> ",
            multiline=False,
        )
        self.log_conversation("user", init_description)
        self.task_log["task description"] = init_description
        # 2. Provide the information to the reasoning session for the task initialization.
        # Note that this information is not parsed by the three-step process in reasoning.
        # It is directly used to initialize the task.
        prefixed_init_description = self.prompts.task_description + init_description
        with self.console.status(
            "[bold green] Constructing Initial Penetration Testing Tree..."
        ) as status:
            _reasoning_response = self.reasoningAgent.send_message(
                prefixed_init_description, self.test_reasoning_session_id
            )
        # 3. Pass to generation session for more details.
        # Note that the generation session is not used for the task initialization.
        with self.console.status("[bold green] Generating Initial Task") as status:
            _generation_response = self.generationAgent.send_message(
                self.prompts.todo_to_command + _reasoning_response,
                self.test_generation_session_id,
            )

        # Display the initial generation result
        response = _reasoning_response + "\n" + _generation_response
        self.console.print("BIKprotect output: ", style="bold green")
        self.console.print(response)
        self.log_conversation("BIKprotect", "BIKprotect output:" + response)

    def initialize(self, previous_session_ids=None):
        # initialize the backbone sessions and test the connection to chatGPT
        # define three sessions: testGenerationSession, testReasoningSession, and InputParsingSession
        if previous_session_ids is not None and self.useAPI is False:
            self.test_generation_session_id = previous_session_ids.get(
                "test_generation", None
            )
            self.test_reasoning_session_id = previous_session_ids.get("reasoning", None)
            self.input_parsing_session_id = previous_session_ids.get("parsing", None)
            # debug the three sessions
            print(f"Previous session ids: {str(previous_session_ids)}")
            print(f"Test generation session id: {str(self.test_generation_session_id)}")
            print(f"Test reasoning session id: {str(self.test_reasoning_session_id)}")
            print(f"Input parsing session id: {str(self.input_parsing_session_id)}")
            print("-----------------")
            self.task_log = previous_session_ids.get("task_log", {})
            self.console.print(f"Task log: {str(self.task_log)}", style="bold green")
            print("You may use discussion function to remind yourself of the task.")

            ## verify that all the sessions are not None
            if (
                self.test_generation_session_id is None
                or self.test_reasoning_session_id is None
                or self.input_parsing_session_id is None
            ):
                self.console.print(
                    "[bold red] Error: the previous session ids are not valid. Loading new sessions"
                )
                self.initialize()

        else:
            with self.console.status(
                "[bold green] Initialize ChatGPT Sessions..."
            ) as status:
                try:
                    (
                        text_0,
                        self.test_generation_session_id,
                    ) = self.generationAgent.send_new_message(
                        self.prompts.generation_session_init,
                    )
                    (
                        text_1,
                        self.test_reasoning_session_id,
                    ) = self.reasoningAgent.send_new_message(
                        self.prompts.reasoning_session_init
                    )
                    (
                        text_2,
                        self.input_parsing_session_id,
                    ) = self.parsingAgent.send_new_message(
                        self.prompts.input_parsing_init
                    )
                except Exception as e:
                    logger.error(e)
            self.console.print("- ChatGPT Sessions Initialized.", style="bold green")
            self._feed_init_prompts()

    def reasoning_handler(self, text) -> str:
        # summarize the contents if necessary.
        if len(text) > self.parsing_char_window:
            text = self.input_parsing_handler(text)
        """
        # pass the information to reasoning_handler and obtain the results
        response = self.reasoningAgent.send_message(
            self.prompts.process_results + text, self.test_reasoning_session_id
        )
        # log the conversation
        """
        # BIKprotect Reasoning Logic
        ## 1. Given the information, update the PTT
        _updated_ptt_response = self.reasoningAgent.send_message(
            self.prompts.process_results + text, self.test_reasoning_session_id
        )
        ## 2. Validate if the PTT is correct
        # TODO
        ## 3. If the PTT is correct, select all the to-dos
        _task_selection_response = self.reasoningAgent.send_message(
            self.prompts.process_results_task_selection, self.test_reasoning_session_id
        )
        # get the complete output:
        response = _updated_ptt_response + _task_selection_response

        self.log_conversation("reasoning", response)
        return response

    def input_parsing_handler(self, text, source=None) -> str:
        prefix = "Please summarize the following input. "
        # do some engineering trick here. Add postfix to the input to make it more understandable by LLMs.
        if source is not None and source in self.postfix_options.keys():
            prefix += self.postfix_options[source]
        # The default token-size limit is 4096 (web UI even shorter). 1 token ~= 4 chars in English
        # Use textwrap to split inputs. Limit to 2000 token (8000 chars) for each input
        # (1) replace all the newlines with spaces
        text = text.replace("\r", " ").replace("\n", " ")
        # (2) wrap the text
        wrapped_text = textwrap.fill(text, 8000)
        wrapped_inputs = wrapped_text.split("\n")
        # (3) send the inputs to chatGPT input_parsing_session and obtain the results
        summarized_content = ""
        for wrapped_input in wrapped_inputs:
            word_limit = f"Please ensure that the input is less than {8000 / len(wrapped_inputs)} words.\n"
            summarized_content += self.parsingAgent.send_message(
                prefix + word_limit + wrapped_input, self.input_parsing_session_id
            )
        # log the conversation
        self.log_conversation("input_parsing", summarized_content)
        return summarized_content

    def test_generation_handler(self, text):
        # send the contents to chatGPT test_generation_session and obtain the results
        response = self.generationAgent.send_message(
            text, self.test_generation_session_id
        )
        # log the conversation
        self.log_conversation("generation", response)
        return response

    def local_input_handler(self) -> str:
        """
        Request for user's input to handle the local task
        """
        local_task_response = ""
        self.chat_count += 1
        local_request_option = local_task_entry()
        self.log_conversation("user", local_request_option)

        if local_request_option == "help":
            print(localTaskCompleter().task_details)

        elif local_request_option == "discuss":
            ## (1) Request for user multi-line input
            self.console.print(
                "Please share your findings and questions with BIKprotect."
            )
            self.log_conversation(
                "BIKprotect",
                "Please share your findings and questions with BIKprotect. (End with <shift + right-arrow>)",
            )
            user_input = prompt_ask("Your input: ", multiline=True)
            self.log_conversation("user", user_input)
            ## (2) pass the information to the reasoning session.
            with self.console.status("[bold green] BIKprotect Thinking...") as status:
                local_task_response = self.test_generation_handler(
                    self.prompts.local_task_prefix + user_input
                )
            ## (3) print the results
            self.console.print("BIKprotect:\n", style="bold green")
            self.console.print(local_task_response + "\n", style="yellow")
            self.log_conversation("BIKprotect", local_task_response)

        elif local_request_option == "brainstorm":
            ## (1) Request for user multi-line input
            self.console.print(
                "Please share your concerns and questions with BIKprotect."
            )
            self.log_conversation(
                "BIKprotect",
                "Please share your concerns and questions with BIKprotect. End with <shift + right-arrow>)",
            )
            user_input = prompt_ask("Your input: ", multiline=True)
            self.log_conversation("user", user_input)
            ## (2) pass the information to the reasoning session.
            with self.console.status("[bold green] BIKprotect Thinking...") as status:
                local_task_response = self.test_generation_handler(
                    self.prompts.local_task_brainstorm + user_input
                )
            ## (3) print the results
            self.console.print("BIKprotect:\n", style="bold green")
            self.console.print(local_task_response + "\n", style="yellow")
            self.log_conversation("BIKprotect", local_task_response)

        elif local_request_option == "google":
            # get the users input
            self.console.print(
                "Please enter your search query. BIKprotect will summarize the info from google. (End with <shift + right-arrow>) ",
                style="bold green",
            )
            self.log_conversation(
                "BIKprotect",
                "Please enter your search query. BIKprotect will summarize the info from google.",
            )
            user_input = prompt_ask("Your input: ", multiline=False)
            self.log_conversation("user", user_input)
            with self.console.status("[bold green] BIKprotect Thinking...") as status:
                # query the question
                result: dict = google_search(user_input, 5)  # 5 results by default
                # summarize the results
                # TODO
                local_task_response = (
                    "Google search results:\n" + "still under development."
                )
            self.console.print(local_task_response + "\n", style="yellow")
            self.log_conversation("BIKprotect", local_task_response)
            return local_task_response

        elif local_request_option == "continue":
            self.console.print("Exit the local task and continue the main task.")
            self.log_conversation(
                "BIKprotect", "Exit the local task and continue the main task."
            )
            local_task_response = "continue"

        return local_task_response

    def input_handler(self) -> str:
        """
        Request for user's input to:
            (1) input test results,
            (2) ask for todos,
            (3) input other information (discuss),
            (4) google.
            (4) end.
        The design details are based on BIKprotect_design.md

        Return
        -----
        response: str
            The response from the chatGPT model.
        """
        self.chat_count += 1

        request_option = main_task_entry()
        self.log_conversation("user", request_option)
        # always check if the session expires.
        # check if session expires
        if not self.useAPI:
            conversation_history = self.parsingAgent.get_conversation_history()
            while conversation_history is None:
                self.refresh_session()
                conversation_history = self.parsingAgent.get_conversation_history()

        if request_option == "help":
            print(mainTaskCompleter().task_details)

        if request_option == "next":
            ## (1) pass the information to input_parsing session.
            ## Give an option list for user to choose from
            options = list(self.postfix_options.keys())
            opt_desc = list(self.options_desc.values())

            value_list = [
                (
                    i,
                    HTML(
                        f'<style fg="cyan">{options[i]}</style><style fg="LightSeaGreen">{opt_desc[i]}</style>'
                    ),
                )
                for i in range(len(options))
            ]
            source = prompt_select(
                title="Please choose the source of the information.", values=value_list
            )
            self.console.print(
                "Your input: (End with <shift + right-arrow>)", style="bold green"
            )
            user_input = prompt_ask("> ", multiline=True)
            self.log_conversation(
                "user", f"Source: {options[int(source)]}" + "\n" + user_input
            )
            with self.console.status("[bold green] BIKprotect Thinking...") as status:
                parsed_input = self.input_parsing_handler(
                    user_input, source=options[int(source)]
                )
                ## (2) pass the summarized information to the reasoning session.
                reasoning_response = self.reasoning_handler(parsed_input)
                self.step_reasoning_response = reasoning_response

            ## (3) print the results
            self.console.print(
                "Based on the analysis, the following tasks are recommended:",
                style="bold green",
            )
            self.console.print(reasoning_response + "\n")
            self.log_conversation(
                "BIKprotect",
                "Based on the analysis, the following tasks are recommended:"
                + reasoning_response,
            )
            response = reasoning_response

        elif request_option == "more":
            self.log_conversation("user", "more")
            ## (1) check if reasoning session is initialized
            if not hasattr(self, "step_reasoning_response"):
                self.console.print(
                    "You have not initialized the task yet. Please perform the basic testing following `next` option.",
                    style="bold red",
                )
                response = "You have not initialized the task yet. Please perform the basic testing following `next` option."
                self.log_conversation("BIKprotect", response)
                return response
            ## (2) start local task generation.
            ### (2.1) ask the reasoning session to analyze the current situation, and explain the task
            self.console.print(
                "BIKprotect will generate more test details, and enter the sub-task generation mode. (Pressing Enter to continue)",
                style="bold green",
            )
            self.log_conversation(
                "BIKprotect",
                "BIKprotect will generate more test details, and enter the sub-task generation mode.",
            )
            input()

            ### (2.2) pass the sub-tasks to the test generation session
            with self.console.status("[bold green] BIKprotect Thinking...") as status:
                generation_response = self.test_generation_handler(
                    self.step_reasoning_response
                )
                _local_init_response = self.test_generation_handler(
                    self.prompts.local_task_init
                )

            self.console.print(
                "Below are the further details.",
                style="bold green",
            )
            self.console.print(generation_response + "\n")
            response = generation_response
            self.log_conversation("BIKprotect", response)

            ### (2.3) local task handler
            while True:
                local_task_response = self.local_input_handler()
                if local_task_response == "continue":
                    # break the local task handler
                    break

        elif request_option == "todo":
            ## log that user is asking for todo list
            self.log_conversation("user", "todo")
            ## (1) ask the reasoning session to analyze the current situation, and list the top sub-tasks
            with self.console.status("[bold green] BIKprotect Thinking...") as status:
                reasoning_response = self.reasoning_handler(self.prompts.ask_todo)
                ## (2) pass the sub-tasks to the test_generation session.
                message = self.prompts.todo_to_command + "\n" + reasoning_response
                generation_response = self.test_generation_handler(message)
                ## (3) print the results
            self.console.print(
                "Based on the analysis, the following tasks are recommended:",
                style="bold green",
            )
            self.console.print(reasoning_response + "\n")
            self.console.print(
                "You can follow the instructions below to complete the tasks.",
                style="bold green",
            )
            self.console.print(generation_response + "\n")
            response = reasoning_response
            self.log_conversation(
                "BIKprotect",
                (
                    (
                        (
                            (
                                "Based on the analysis, the following tasks are recommended:"
                                + response
                            )
                            + "\n"
                        )
                        + "You can follow the instructions below to complete the tasks."
                    )
                    + generation_response
                ),
            )
        elif request_option == "discuss":
            ## (1) Request for user multi-line input
            self.console.print(
                "Please share your thoughts/questions with BIKprotect. (End with <shift + right-arrow>) "
            )
            self.log_conversation(
                "BIKprotect", "Please share your thoughts/questions with BIKprotect."
            )
            user_input = prompt_ask("Your input: ", multiline=True)
            self.log_conversation("user", user_input)
            ## (2) pass the information to the reasoning session.
            with self.console.status("[bold green] BIKprotect Thinking...") as status:
                response = self.reasoning_handler(self.prompts.discussion + user_input)
            ## (3) print the results
            self.console.print("BIKprotect:\n", style="bold green")
            self.console.print(response + "\n", style="yellow")
            self.log_conversation("BIKprotect", response)

        elif request_option == "google":
            # get the users input
            self.console.print(
                "Please enter your search query. BIKprotect will summarize the info from google. (End with <shift + right-arrow>) ",
                style="bold green",
            )
            self.log_conversation(
                "BIKprotect",
                "Please enter your search query. BIKprotect will summarize the info from google.",
            )
            user_input = prompt_ask("Your input: ", multiline=False)
            self.log_conversation("user", user_input)
            with self.console.status("[bold green] BIKprotect Thinking...") as status:
                # query the question
                result: dict = google_search(user_input, 5)  # 5 results by default
                # summarize the results
                # TODO
                response = "Google search results:\n" + "still under development."
            self.console.print(response + "\n", style="yellow")
            self.log_conversation("BIKprotect", response)
            return response

        elif request_option == "quit":
            response = False
            self.console.print("Thank you for using BIKprotect!", style="bold green")
            self.log_conversation("BIKprotect", "Thank you for using BIKprotect!")

        else:
            self.console.print("Please key in the correct options.", style="bold red")
            self.log_conversation("BIKprotect", "Please key in the correct options.")
            response = "Please key in the correct options."
        return response

    def save_session(self):
        """
        Save the current session for next round of usage.
        The test information is saved in the directory `./test_history`
        """
        self.console.print(
            "Before you quit, you may want to save the current session.",
            style="bold green",
        )
        # 1. Require a save name from the user. If not, use the current time as the save name.
        save_name = prompt_ask(
            "Please enter the name of the current session. (Default with current timestamp)\n> ",
            multiline=False,
        )
        if save_name == "":
            save_name = str(time.time())
        # 2. Save the current session
        with open(
            os.path.join(
                os.path.realpath(os.path.dirname(__file__)),
                os.pardir,
                os.pardir,
                self.save_dir,
                save_name,
            ),
            "w",
        ) as f:
            # store the three ids and task_log
            session_ids = {
                "reasoning": self.test_reasoning_session_id,
                "test_generation": self.test_generation_session_id,
                "parsing": self.input_parsing_session_id,
                "task_log": self.task_log,
            }
            json.dump(session_ids, f)
        self.console.print(
            f"The current session is saved as {save_name}", style="bold green"
        )
        return

    def _preload_session(self) -> dict:
        """
        Preload the session from the save directory.

        Returns:
            dict: the session ids for the three sessions.
            None if no previous session is found.
        """
        if continue_from_previous := confirm(
            "Do you want to continue from previous session?"
        ):
            # load the filenames from the save directory
            filenames = os.listdir(
                os.path.join(
                    os.path.realpath(os.path.dirname(__file__)),
                    os.pardir,
                    os.pardir,
                    self.save_dir,
                )
            )
            if len(filenames) == 0:
                print("No previous session found. Please start a new session.")
                return None
            else:  # print all the files
                print("Please select the previous session by its index (integer):")
                for i, filename in enumerate(filenames):
                    print(f"{str(i)}. {filename}")
                # ask for the user input
                try:
                    previous_testing_name = filenames[
                        int(input("Please key in your option (integer): "))
                    ]
                    print(f"You selected: {previous_testing_name}")
                except ValueError as e:
                    print("You input an invalid option. Will start a new session.")
                    return None

        elif continue_from_previous is False:
            return None
        else:
            print("You input an invalid option. Will start a new session.")
            return None
        # 2. load the previous session information
        if previous_testing_name is not None:
            # try to load the file content with json
            try:
                with open(
                    os.path.join(
                        os.path.realpath(os.path.dirname(__file__)),
                        os.pardir,
                        os.pardir,
                        self.save_dir,
                        previous_testing_name,
                    ),
                    "r",
                ) as f:
                    return json.load(f)
            except Exception as e:
                print(
                    "Error when loading the previous session. The file name is not correct"
                )
                print(e)
                previous_testing_name = None
                return None

    def main(self):
        """
        The main function of BIKprotect. The design is based on BIKprotect_design.md
        """
        # 0. initialize the backbone sessions and test the connection to chatGPT
        loaded_ids = self._preload_session()
        self.initialize(previous_session_ids=loaded_ids)

        # enter the main loop.
        while True:
            try:
                result = self.input_handler()
                self.console.print(
                    "-----------------------------------------", style="bold white"
                )
                if not result:  # end the session
                    break
            except Exception as e:  # catch all general exception.
                # log the exception
                self.log_conversation("exception", str(e))
                # print the exception
                self.console.print(f"Exception: {str(e)}", style="bold red")
                # add a more detailed debugging
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                self.console.print(
                    "Exception details are below. You may submit an issue on github and paste the error trace",
                    style="bold green",
                )
                # self.console.print(exc_type, fname, exc_tb.tb_lineno)
                print(traceback.format_exc())
                # safely quit the session
                break
        # log the session. Save self.history into a txt file based on timestamp
        timestamp = time.time()
        log_name = f"BIKprotect_log_{str(timestamp)}.txt"
        # save it in the logs folder
        log_path = os.path.join(self.log_dir, log_name)
        with open(log_path, "w") as f:
            json.dump(self.history, f)

        # save the sessions; continue from previous testing
        self.save_session()


if __name__ == "__main__":
    BIKprotect = BIKprotect()
    BIKprotect.main()
