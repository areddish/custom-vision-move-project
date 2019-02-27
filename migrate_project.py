# Migrate a project

import os
import sys
import time

import argparse

from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.training.models import ImageUrlCreateBatch, ImageUrlCreateEntry, Region

def migrate_tags(src_trainer, dest_trainer, project_id, dest_project_id):
    tags =  src_trainer.get_tags(project_id)
    print ("Found:", len(tags), "tags")
    # Re-create all of the tags and store them for look-up
    created_tags = {}
    for tag in src_trainer.get_tags(project_id):
        print ("Creating tag:", tag.name, tag.id)
        created_tags[tag.id] = dest_trainer.create_tag(dest_project_id, tag.name, description=tag.description).id
    return created_tags

def migrate_images(src_trainer, dest_trainer, project_id, dest_project_id, created_tags):
    # Migrate any tagged images that may exist and preserve their tags and regions.
    count = src_trainer.get_tagged_image_count(project_id)
    print ("Found:",count,"tagged images.")
    migrated = 0
    while(count > 0):
        count_to_migrate = min(count, 50)
        print ("Getting", count_to_migrate, "images")
        images = src_trainer.get_tagged_images(project_id, take=count_to_migrate, skip=migrated)
        for i in images:
            print ("Migrating", i.id, i.resized_image_uri)
            regions = []
            if i.regions != None:
                for r in i.regions:
                    print ("Found region:", r.region_id, r.tag_id, r.left, r.top, r.width, r.height)
                    regions.append(Region(tag_id=created_tags[r.tag_id], left=r.left, top=r.top, width=r.width, height=r.height))
            
            if regions.count > 0:
                entry = ImageUrlCreateEntry(url=i.resized_image_uri, regions=regions)
            else:
                    entry = ImageUrlCreateEntry(url=i.resized_image_uri)

            dest_trainer.create_images_from_urls(dest_project_id, images=[entry])
        migrated += count_to_migrate
        count -= count_to_migrate

    # Migrate any untagged images that may exist.
    count = src_trainer.get_untagged_image_count(project_id)
    print ("Found:", count, "untagged images.")
    migrated = 0
    while(count > 0):
        count_to_migrate = min(count, 50)
        print ("Getting", count_to_migrate, "images")
        images = src_trainer.get_untagged_images(project_id, take=count_to_migrate, skip=migrated)
        for i in images:
            print ("Migrating", i.id, i.image_uri)
            regions = []
            if i.regions != None:
                for r in i.regions:
                    print ("Found region:", r.region_id, r.tag_id, r.left, r.top, r.width, r.height)
                    regions.append(Region(tag_id=created_tags[r.tag_id], left=r.left, top=r.top, width=r.width, height=r.height))
            
            if regions.count > 0:
                entry = ImageUrlCreateEntry(url=i.image_uri, regions=regions)
            else:
                    ImageUrlCreateEntry(url=i.image_uri) 

            dest_trainer.create_images_from_urls(dest_project_id, images=[entry])
        migrated += count_to_migrate
        count -= count_to_migrate
    return images

def migrate_project(src_trainer, dest_trainer, project_id):
    # Get the original project
    src_project = src_trainer.get_project(project_id)
    # Create the destination project
    return dest_trainer.create_project(src_project.name, description=src_project.description, domain_id=src_project.settings.domain_id)

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-p", "--project", action="store", type=str, help="Source project ID", dest="project_id", default=None)
    arg_parser.add_argument("-s", "--src", action="store", type=str, help="Source Training-Key", dest="source_training_key", default=None)
    arg_parser.add_argument("-se", "--srcendpoint", action="store", type=str, help="Source endpoint URL", dest="source_url", default=None)
    arg_parser.add_argument("-d", "--dest", action="store", type=str, help="Destination Training-Key", dest="destination_training_key", default=None)
    arg_parser.add_argument("-de", "--destendpoint", action="store", type=str, help="Destination endpoint URL", dest="destination_url", default=None)
    args = arg_parser.parse_args()

    if (not args.project_id or not args.source_training_key or not args.destination_training_key):
        arg_parser.print_help()
        exit(-1)

    print ("Collecting information for source project:", args.project_id)

    # Client for Source
    src_trainer = CustomVisionTrainingClient(args.source_training_key, endpoint=args.source_url)

    # Client for Destination
    dest_trainer = CustomVisionTrainingClient(args.destination_training_key, endpoint=args.destination_url)

    destination_project = migrate_project(src_trainer, dest_trainer, args.project_id)
    tags = migrate_tags(src_trainer, dest_trainer, args.project_id, destination_project.id)
    source_images = migrate_images(src_trainer, dest_trainer, args.project_id, destination_project.id, tags)