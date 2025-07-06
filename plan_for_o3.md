We are planning to create a tool that humanists can use for doing visual semiotics on disparate collections of images they have gathered. My current rough plan is that we would have:

1. A simple CLIP based system for generating various simple keyphrase similarity estimates and whatnot. Below will be a summary of an existing draft of a system.

2. A more complex openAI endpoint based system to aid in in doing AI-assisted MultiModal Content analysis a la Serafini & Reid. Here the idea is that we first use an LLM to convert a textual description of a template into a prompt that can be passed along with an image to extract quantitative analysis data of the image. By using that template-based prompt with all images in a dataset, we can turn subject the images to a more automated quantitative analysis. Below will be a summary of an existing draft of a system that does quantitative MMC with a single prompt, together with the prompt. We've also used o3-Pro to generate a first draft of a metaprompt that would convert a humanist's analysis template into a prompt that we can use for the analysis.

3. The main system would allow a user to upload a batch of images. The user then has a chance of giving either a list of phrases to use with a CLIP based evaluation, and/or an analysis template that will trigger a bigger analysis. The user should have the option to edit the prompt generated from their analysis template as needed. After running the AI-assisted analyses to extract quantitative data from the images, the system then should run a compherensive list of tests where we look for correlations between any of the dimensions measured, including but not limited to any locational or temporal data that we might gather from image EXIF data.

I will also include a snippet of a conversation I've had with a fellow researcher, expressing interest in the benefits that such a system might bring.

After ingesting all of this, your task is to rewrite this as a project description/specification that I will submit to an LLM-based system generator like Replit or Lovable. That system will have to go on based on just your specification, so please make it thorough!
