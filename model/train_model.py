"""
train_model.py
================
Trains a real plant-disease classifier using transfer learning on
MobileNetV2, fine-tuned on the PlantVillage dataset (38 classes).

USAGE
-----
1. Download the PlantVillage dataset (color images), e.g. from Kaggle:
   https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset

2. Arrange it as:
     data/
       train/
         Apple___Apple_scab/
         Apple___Black_rot/
         ... (one folder per class)
       val/
         Apple___Apple_scab/
         ...

3. Run:
     python model/train_model.py --data_dir data --epochs 15

4. The trained model is saved to model/plant_disease_model.h5.
   Restart the Flask app afterwards — it will automatically pick up
   the trained model and stop using demo mode.

Requires: tensorflow>=2.15
"""

import argparse
import json
import os

import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator

IMG_SIZE = (224, 224)
BATCH_SIZE = 32


def build_model(num_classes: int) -> tf.keras.Model:
    base = MobileNetV2(input_shape=IMG_SIZE + (3,), include_top=False, weights="imagenet")
    base.trainable = False  # freeze for initial training; unfreeze later to fine-tune

    inputs = layers.Input(shape=IMG_SIZE + (3,))
    x = base(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data", help="Folder containing train/ and val/ subfolders")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--fine_tune_epochs", type=int, default=5)
    parser.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "plant_disease_model.h5"))
    args = parser.parse_args()

    train_dir = os.path.join(args.data_dir, "train")
    val_dir = os.path.join(args.data_dir, "val")

    train_gen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=25,
        width_shift_range=0.1,
        height_shift_range=0.1,
        shear_range=0.1,
        zoom_range=0.15,
        horizontal_flip=True,
        fill_mode="nearest",
    ).flow_from_directory(train_dir, target_size=IMG_SIZE, batch_size=BATCH_SIZE, class_mode="categorical")

    val_gen = ImageDataGenerator(rescale=1.0 / 255).flow_from_directory(
        val_dir, target_size=IMG_SIZE, batch_size=BATCH_SIZE, class_mode="categorical"
    )

    num_classes = train_gen.num_classes
    model = build_model(num_classes)

    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=4, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=2),
    ]

    print(f"Training head on {num_classes} classes...")
    model.fit(train_gen, validation_data=val_gen, epochs=args.epochs, callbacks=callbacks)

    # Fine-tune: unfreeze the base model's top layers for a few more epochs
    print("Fine-tuning base model...")
    base_model = model.layers[1]
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.fit(train_gen, validation_data=val_gen, epochs=args.fine_tune_epochs, callbacks=callbacks)

    model.save(args.out)
    print(f"Model saved to {args.out}")

    # Save the class index mapping so labels.json can be regenerated/checked
    class_indices = train_gen.class_indices
    index_to_class = {v: k for k, v in class_indices.items()}
    with open(os.path.join(os.path.dirname(args.out), "class_indices.json"), "w") as f:
        json.dump(index_to_class, f, indent=2)
    print("Saved class index mapping to model/class_indices.json — "
          "use it to double check model/labels.json ordering matches your dataset.")


if __name__ == "__main__":
    main()
