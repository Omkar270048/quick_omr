# import omr_processing
#
#
# omr_processing.process_image("final_template_omr_filled.png")
# omr_data = omr_processing.answer
#
# print(omr_data)


import black_white

input_path = 'Document 31_1 (2) (1).jpg'
output_path = 'uploads/image.png'

black_white.convert_to_black_and_white(input_path, output_path)
