import os

files = ['ml/train.py', 'ml/model.py']

fixes = [
    ('from tensorflow import keras', 'import keras'),
    ('from tensorflow.keras', 'from keras'),
    ('tf.keras', 'keras'),
]

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in fixes:
        content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(filepath + ' fixed')

print('Done!')