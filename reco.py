import face_recognition
import os

TRUE_DIR1 = input("Enter True directory name (Must be in the script's directory): ")
FALSE_DIR1 = input("Enter False directory name (Must be in the script's directory): ")

TRUE_DIR = os.listdir(f'{TRUE_DIR1}')
FALSE_DIR = os.listdir(f'{FALSE_DIR1}')

for t in TRUE_DIR:
    try:
        true = face_recognition.load_image_file(f'./{TRUE_DIR1}/{t}')
        true_enc = face_recognition.face_encodings(true)[0]
    except:
        pass


    for f in FALSE_DIR:
        try:
            false = face_recognition.load_image_file(f'./{FALSE_DIR1}/{f}')
            false_enc = face_recognition.face_encodings(false)[0]

            results = face_recognition.compare_faces([true_enc], false_enc)

            if results[0]:
                print(f'True Match: {f}')

            else:
                print(f'False Match: {f}')
        except:
            print(f'Cant detect faces with this picture! {f}')