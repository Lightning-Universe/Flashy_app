import flash
from flash.core.data.utils import download_data
from flash.image import ImageClassificationData, ImageClassifier

download_data("{{ url }}", ".")

datamodule = ImageClassificationData.from_{{ method }}(
    {% for key, value in data_config.items() %}{{ key }}={% if value is string %}"{{ value }}"{% else %}{{ value }}{% endif %},{% endfor %}
    batch_size=4,
    transform_kwargs={"image_size": (196, 196), "mean": (0.485, 0.456, 0.406), "std": (0.229, 0.224, 0.225)},
)

model = ImageClassifier(backbone="{{ model_config.backbone }}", learning_rate={{ model_config.learning_rate }}, labels=datamodule.labels)

trainer = flash.Trainer(max_epochs=1, limit_train_batches=10, limit_val_batches=10)
trainer.finetune(model, datamodule=datamodule, strategy="freeze")

{% if not rendering %}
import os
trainer.save_checkpoint(os.path.join("{{ root }}", "{{ run_id }}.pt"))
with open(os.path.join("{{ root }}", '{{ run_id }}.txt'), 'w') as f:
    f.write(f"{trainer.callback_metrics['val_accuracy']}")
{% endif %}
