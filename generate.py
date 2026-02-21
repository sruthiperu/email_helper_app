from openai import OpenAI
from dotenv import load_dotenv
import os
import yaml
import json

load_dotenv()

with open("prompts.yaml", "r") as f:
    prompts = yaml.safe_load(f)

class GenerateEmail():    
    def __init__(self, model: str):
        # initialize client once
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.deployment_name = model
        self.judge_model = "gpt-4.1"

    def _call_api(self, messages, is_judge=False):
        selected_model = "gpt-4.1" if is_judge else self.deployment_name
        response = self.client.chat.completions.create(
            model=selected_model,
            messages=messages,
            temperature=0
            # max_tokens=250 
        )

        print(response.choices[0].message.content)
        return response.choices[0].message.content
    
    def get_prompt(self, prompt_name, prompt_type='user', **kwargs):
        template = prompts[prompt_name][prompt_type]
        return template.format(**kwargs)
    
    def send_prompt(self, user_prompt: str, system_msg="You are a helpful assistant."):
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt}
        ]
        return self._call_api(messages)
    
    def generate(self, action: str, text: str = None, **kwargs) -> str:
        if not text:
            text = "Hello World!"

        if action == "shorten":
            args = {
                "selected_text": text
            }
            system_prompt = self.get_prompt('shorten', prompt_type='system', **args)
            user_prompt = self.get_prompt('shorten', **args)
            print("system prompt:", system_prompt)
            print("user prompt:", user_prompt)
            model_response = self.send_prompt(user_prompt, system_prompt)
            return model_response
        
        elif action == "lengthen":
            args = {
                "selected_text": text
            }
            system_prompt = self.get_prompt('lengthen', prompt_type='system', **args)
            user_prompt = self.get_prompt('lengthen', **args)
            print("system prompt:", system_prompt)
            print("user prompt:", user_prompt)
            model_response = self.send_prompt(user_prompt, system_prompt)
            return model_response
        
        elif action == "change_tone":
            tone = kwargs.get("tone", "friendly")
            args = {
                "selected_text": text,
                "tone": tone
            }
            system_prompt = self.get_prompt('change_tone', prompt_type='system', **args)
            user_prompt = self.get_prompt('change_tone', **args)
            print("system prompt:", system_prompt)
            print("user prompt:", user_prompt)
            model_response = self.send_prompt(user_prompt, system_prompt)
            return model_response
    
    def judge_faithfulness(self, original_email: str, edited_email: str) -> dict:
        args = {
            "selected_text": original_email,
            "model_response": edited_email
        }

        system_prompt = self.get_prompt('faithfulness_judge', prompt_type='system', **args)
        user_prompt = self.get_prompt('faithfulness_judge', **args)
        model_rating = self.send_prompt(user_prompt, system_prompt)
        return json.loads(model_rating)
    
    def judge_completeness(self, instruction: str, original_email: str, edited_email: str) -> dict:
        args = {
            "instruction": instruction,
            "selected_text": original_email,
            "model_response": edited_email
        }

        system_prompt = self.get_prompt('completeness_judge', prompt_type='system', **args)
        user_prompt = self.get_prompt('completeness_judge', **args)
        model_rating = self.send_prompt(user_prompt, system_prompt)
        return json.loads(model_rating)


"""
if __name__ == "__main__":
    gen = GenerateEmail(model="gpt-4o-mini")
    res = gen.generate("lengthen")
    print("\nResult:")
    print(res)
"""