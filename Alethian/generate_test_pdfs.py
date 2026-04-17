from fpdf import FPDF
import os

def create_pdf(filename, title, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16, style='B')
    pdf.cell(200, 10, txt=title, ln=1, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    
    # Split text into manageable chunks for multi_cell
    for paragraph in content.split("\n\n"):
        pdf.multi_cell(0, 10, txt=paragraph.replace("\n", " "))
        pdf.ln(5)
        
    pdf.output(filename)

# 1. Pure Web Plagiarism (Copied from Wikipedia on Quantum Mechanics)
web_content = """
Quantum mechanics is a fundamental theory in physics that describes the physical properties of nature at the scale of atoms and subatomic particles. It is the foundation of all quantum physics including quantum chemistry, quantum field theory, quantum technology, and quantum information science.

Classical physics, the collection of theories that existed before the advent of quantum mechanics, describes many aspects of nature at an ordinary (macroscopic) scale, but is not sufficient for describing them at small (atomic and subatomic) scales. Most theories in classical physics can be derived from quantum mechanics as an approximation valid at large (macroscopic) scale.

Quantum mechanics differs from classical physics in that energy, momentum, angular momentum, and other quantities of a bound system are restricted to discrete values (quantization); objects have characteristics of both particles and waves (wave-particle duality); and there are limits to how accurately the value of a physical quantity can be predicted prior to its measurement, given a complete set of initial conditions (the uncertainty principle).
"""

# 2. Original Internal Base (Unique story about a fictional machine learning model)
internal_base_content = """
The Quantum-Neuro Interface (QNI) is a theoretical framework proposed by Dr. Aris Thorne in 2045. It bridges the gap between quantum superposition states and human biological neural networks. Unlike traditional BCIs (Brain-Computer Interfaces), the QNI does not rely on electrical impulses measured via EEG or intracranial electrodes. Instead, it utilizes entangled particle pairs to map cognitive intent directly into a digital substrate.

Initial experiments conducted at the Geneva Research Institute demonstrated a 99.8% fidelity rate in translating thought into text, though the system required the user to be immersed in a hyper-cooled quantum stabilization chamber. The primary hurdle remains the decoherence problem: biological systems are inherently noisy and warm, causing the entangled pairs to collapse prematurely.

Dr. Thorne's paper suggests that by introducing a localized Bose-Einstein condensate near the hippocampus, the decoherence time could be extended from milliseconds to several seconds, providing enough window for complex abstract thoughts to be digitized. This marks a significant leap in cognitive augmentation technologies.
"""

# 3. Internal Plagiarism (Same as base, but paraphrased)
internal_plagiarism_content = """
The Quantum-Neuro Interface, or QNI, is a theoretical concept introduced by Dr. Aris Thorne around the year 2045. It connects human biological neural networks with quantum superposition states. In contrast to standard Brain-Computer Interfaces (BCIs), QNI doesn't depend on electrical signals gathered from EEG caps or brain electrodes. Rather, it uses pairs of entangled particles to directly translate cognitive intentions into a computer environment.

Early testing done at the Geneva Research Institute showed an accuracy of 99.8% when turning thoughts into written words. However, the subjects had to be placed inside a highly refrigerated quantum stabilization room. The main challenge is still the issue of decoherence: organic bodies are naturally warm and full of interference, which makes the entangled particles lose their state too quickly.

In his research, Dr. Thorne proposes that placing a small Bose-Einstein condensate close to the brain's hippocampus might stretch the decoherence duration from a few milliseconds up to a couple of seconds. This would give sufficient time to record complicated and abstract ideas, representing a huge step forward in the field of mental enhancement tools.
"""

os.makedirs('test_pdfs', exist_ok=True)
create_pdf("test_pdfs/Test_1_Web_Plagiarism.pdf", "Quantum Mechanics Overview", web_content)
create_pdf("test_pdfs/Test_2_Internal_Original.pdf", "The QNI Framework", internal_base_content)
create_pdf("test_pdfs/Test_3_Internal_Paraphrased.pdf", "Advances in QNI Tech", internal_plagiarism_content)

print("Test PDFs generated successfully in the 'test_pdfs' folder.")
