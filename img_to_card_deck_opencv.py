from PIL import Image
import os, os.path
import numpy as np
import cv2
import json
import sys

def import_images(path):
    valid_images = [".jpg",".png",".jpeg", ".gif",".tga"]

    imgs = []
    names = []
    for f in os.listdir(path):
        ext = os.path.splitext(f)[1]
        if ext.lower() not in valid_images:
            continue

        # store file name in names, remove extension
        names.append(os.path.splitext(f)[0])
        imgs.append(Image.open(os.path.join(path,f)))
    return [names, imgs]

def generate_action_cord(start, diff):
    cords = []
    for y in range(5):
        for x in range(6):
            a = start[0] + x * diff[0]
            b = start[1] + y * diff[1]
            c = start[0] + (x + 1) * diff[0]
            d = start[1] + (y + 1) * diff[1]
            cords.append([a, b, c, d])
    return cords

def generate_ch_cord(start, diff):
    cords = []
    for x in range(3):
        a = start[0] + x * diff[0]
        b = start[1]
        c = start[0] + (x + 1) * diff[0]
        d = start[1] + diff[1]
        cords.append([a, b, c, d])
    return cords

def crop_image(img, cords):
    result = []
    for cord in cords:
        result.append(img.crop(cord))
    return result


def export_images(imgs, path, name):
    if not os.path.exists(path):
            os.makedirs(path)
    for idx, img in enumerate(imgs):
        file_name = f"{path}/{name}_{idx}.jpg"
        img.save(file_name)
        print(f"saved {file_name}")

def cropped_img_match_template(img, names, templates):
    result = ""
    max = 0
    for idx,temp in enumerate(templates):
        cur_result = cv2.matchTemplate(img, temp, cv2.TM_CCOEFF_NORMED)
        cur_max = np.amax(cur_result)
        cur_name = names[idx]

        # return early with high correlation
        if cur_max > 0.9:
            result = cur_name
            break

        # update template choice
        if cur_max > max:
            max = cur_max
            result = cur_name
            # print(f"max = {cur_max} for {cur_name}")
    return result

def imgs_to_arrays(imgs):
    result = []
    for img in imgs:
        result.append(np.array(img)[:,:,:3])
    return result


def convert_one_to_csv(image_path):
    ret = []
    new_size = (1200, 1630)
    original_img = Image.open(os.path.join(image_path)).resize(new_size)
    print(f"converting {image_path} to csv data")

    # convert cropped characters
    cropped_img_arrays = imgs_to_arrays(crop_image(original_img, ch_cords))
    for img in cropped_img_arrays:
            result = cropped_img_match_template(img, character_names, character_templates_arrays)
            if result == "empty":
                ret.append('')
            else:
                ret.append(result)

    # convert cropped actions
    cropped_img_arrays = imgs_to_arrays(crop_image(original_img, ac_cords))
    for img in cropped_img_arrays:
        result = cropped_img_match_template(img, action_names, action_template_arrays)
        if result == "empty":
            ret.append('')
        else:
            ret.append(result)
        
    print(ret)
    return ret
    
def convert_one_to_json(image_path, export_path):
    character_results = []
    action_results = []
    new_size = (1200, 1630)
    original_img = Image.open(os.path.join(image_path))
    if original_img.size[0] > 4096 or original_img.size[0] > 4096:
        print("Image too large. Image size:", original_img.size)
        sys.exit(1)
    original_img = original_img.resize(new_size)
    print(f"converting {image_path} to json data")

    # convert cropped characters
    cropped_img_arrays = imgs_to_arrays(crop_image(original_img, ch_cords))
    for img in cropped_img_arrays:
        result = cropped_img_match_template(img, character_names, character_templates_arrays)
        if result == "empty":
            break
        else:
            character_results.append(result)

    # convert cropped actions
    cropped_img_arrays = imgs_to_arrays(crop_image(original_img, ac_cords))
    for img in cropped_img_arrays:
        result = cropped_img_match_template(img, action_names, action_template_arrays)
        if result == "empty":
            break
        else:
            action_results.append(result)

    x = {
        "characters": character_results,
        "actions": action_results
    }

    output_file = open(export_path, "w", encoding='utf-8')
    json.dump(x, output_file, ensure_ascii=False)


# upper left corner: 242 510
# each card size: 115 180
def convert_many(image_path):

    names, original_imgs = import_images(image_path)
    new_size = (1200, 1630)
    resized_imgs = map(lambda im: im.resize(new_size), original_imgs)

    for idx, original_img in enumerate(resized_imgs):

        # seperate character cards       
        print(f"starting image {names[idx]}")
        start = [340, 175]
        diff = [163, 243]
        cords = generate_ch_cord(start, diff)
        # print(cords)
        # cropped_img = crop_image(original_img, cords)
        # export_images(cropped_img, "results/cropped_test", "character")
        # break

        # match template for each character, break if is empty
        cropped_img_arrays = imgs_to_arrays(crop_image(original_img, cords))
        character_results = []
        for img in cropped_img_arrays:
            result = cropped_img_match_template(img, character_names, character_templates_arrays)
            if result == "empty":
                break
            character_results.append(result)
        
        # seperate action cards
        start = [242, 510]
        diff = [115, 180]
        cords = generate_action_cord(start, diff)
        cropped_img_arrays = imgs_to_arrays(crop_image(original_img, cords))
        
        # export_path = "d:/Git/TcgOcr/results/cropped_test"
        # export_images(cropped_imgs, export_path, names[0])

        # match template for each action, break if is empty
        action_results = []
        for img in cropped_img_arrays:
            result = cropped_img_match_template(img, action_names, action_template_arrays)
            if result == "empty":
                break
            action_results.append(result)

        x = {
            "characters": character_results,
            "actions": action_results
        }
        print(character_results)
        print(action_results)
        print()
        directory = "script/img_to_deck/json"
        if not os.path.exists(directory):
            os.makedirs(directory)
        output_file = open(f"{directory}/{names[idx]}.json", "w", encoding='utf-8')
        json.dump(x, output_file, ensure_ascii=False)


# global variables

# templates located in TQLibData, in the same folder as tql-backend
# import character templates
character_template_path = "../../TQLibData/image/tcg/templates/characters"
character_names, character_images = import_images(character_template_path)
character_templates_arrays = imgs_to_arrays(character_images)

# import action templates
action_template_path = "../../TQLibData/image/tcg/templates/actions"
action_names, action_images = import_images(action_template_path)
action_template_arrays = imgs_to_arrays(action_images)

# generate character cords
ch_start = [340, 175]
ch_diff = [163, 243]
ch_cords = generate_ch_cord(ch_start, ch_diff)

# generate action cords
ac_start = [242, 510]
ac_diff = [115, 180]
ac_cords = generate_action_cord(ac_start, ac_diff)

# convert_one_to_json(sys.argv[1], sys.argv[2])
# os.remove(sys.argv[1])
