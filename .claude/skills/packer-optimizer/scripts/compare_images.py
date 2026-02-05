#!/usr/bin/env python3
"""
Packer Image Comparison Tool

Compares Packer build artifacts (AMIs, Docker images) to identify size changes
and potential bloat sources.

Usage:
    # Compare two AMIs
    python compare_images.py ami-12345 ami-67890 --type ami
    
    # Compare two Docker images
    python compare_images.py image:v1.0 image:v2.0 --type docker
    
    # Compare with detailed analysis
    python compare_images.py ami-12345 ami-67890 --type ami --detailed
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class ImageInfo:
    """Information about an image."""
    id: str
    size_bytes: int
    creation_date: str
    metadata: Dict
    
    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def size_gb(self) -> float:
        """Size in gigabytes."""
        return self.size_bytes / (1024 * 1024 * 1024)


class AMIComparator:
    """Compares AWS AMIs."""
    
    def get_ami_info(self, ami_id: str) -> ImageInfo:
        """Get information about an AMI."""
        try:
            cmd = [
                'aws', 'ec2', 'describe-images',
                '--image-ids', ami_id,
                '--query', 'Images[0]',
                '--output', 'json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            ami_data = json.loads(result.stdout)
            
            # Get block device size
            size_bytes = 0
            if 'BlockDeviceMappings' in ami_data:
                for bdm in ami_data['BlockDeviceMappings']:
                    if 'Ebs' in bdm and 'VolumeSize' in bdm['Ebs']:
                        # VolumeSize is in GB
                        size_bytes += bdm['Ebs']['VolumeSize'] * 1024 * 1024 * 1024
            
            return ImageInfo(
                id=ami_id,
                size_bytes=size_bytes,
                creation_date=ami_data.get('CreationDate', 'Unknown'),
                metadata={
                    'name': ami_data.get('Name', 'Unknown'),
                    'description': ami_data.get('Description', ''),
                    'tags': ami_data.get('Tags', []),
                }
            )
        except subprocess.CalledProcessError as e:
            print(f"Error querying AMI {ami_id}: {e.stderr}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing AMI data: {e}", file=sys.stderr)
            sys.exit(1)
    
    def get_ami_snapshot_details(self, ami_id: str) -> List[Dict]:
        """Get detailed snapshot information for an AMI."""
        try:
            # Get AMI details
            cmd = [
                'aws', 'ec2', 'describe-images',
                '--image-ids', ami_id,
                '--query', 'Images[0].BlockDeviceMappings[*].Ebs.SnapshotId',
                '--output', 'json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            snapshot_ids = json.loads(result.stdout)
            
            details = []
            for snapshot_id in snapshot_ids:
                cmd = [
                    'aws', 'ec2', 'describe-snapshots',
                    '--snapshot-ids', snapshot_id,
                    '--query', 'Snapshots[0]',
                    '--output', 'json'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                snapshot_data = json.loads(result.stdout)
                details.append(snapshot_data)
            
            return details
        except Exception as e:
            print(f"Warning: Could not get snapshot details: {e}", file=sys.stderr)
            return []


class DockerComparator:
    """Compares Docker images."""
    
    def get_docker_info(self, image_ref: str) -> ImageInfo:
        """Get information about a Docker image."""
        try:
            # Inspect image
            cmd = ['docker', 'inspect', image_ref]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            image_data = json.loads(result.stdout)[0]
            
            return ImageInfo(
                id=image_ref,
                size_bytes=image_data.get('Size', 0),
                creation_date=image_data.get('Created', 'Unknown'),
                metadata={
                    'repo_tags': image_data.get('RepoTags', []),
                    'repo_digests': image_data.get('RepoDigests', []),
                    'layers': len(image_data.get('RootFS', {}).get('Layers', [])),
                }
            )
        except subprocess.CalledProcessError as e:
            print(f"Error querying Docker image {image_ref}: {e.stderr}", file=sys.stderr)
            sys.exit(1)
        except (json.JSONDecodeError, IndexError) as e:
            print(f"Error parsing Docker image data: {e}", file=sys.stderr)
            sys.exit(1)
    
    def get_layer_details(self, image_ref: str) -> List[Dict]:
        """Get detailed layer information for a Docker image."""
        try:
            cmd = ['docker', 'history', '--no-trunc', '--format', 
                   '{{.Size}}\t{{.CreatedBy}}', image_ref]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            layers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t', 1)
                    size_str = parts[0]
                    command = parts[1] if len(parts) > 1 else ''
                    
                    # Parse size
                    size_bytes = self._parse_size(size_str)
                    
                    layers.append({
                        'size_bytes': size_bytes,
                        'command': command,
                    })
            
            return layers
        except Exception as e:
            print(f"Warning: Could not get layer details: {e}", file=sys.stderr)
            return []
    
    def _parse_size(self, size_str: str) -> int:
        """Parse Docker size string to bytes."""
        size_str = size_str.strip().upper()
        
        if size_str == '0B' or size_str == '0':
            return 0
        
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
        }
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                try:
                    value = float(size_str[:-len(suffix)])
                    return int(value * multiplier)
                except ValueError:
                    return 0
        
        return 0


class ImageComparator:
    """Main image comparison orchestrator."""
    
    def __init__(self, image_type: str):
        self.image_type = image_type
        if image_type == 'ami':
            self.comparator = AMIComparator()
        elif image_type == 'docker':
            self.comparator = DockerComparator()
        else:
            raise ValueError(f"Unsupported image type: {image_type}")
    
    def compare(self, image1_id: str, image2_id: str, detailed: bool = False):
        """Compare two images and print report."""
        print(f"Comparing {self.image_type.upper()} images...")
        print()
        
        # Get image info
        if self.image_type == 'ami':
            image1 = self.comparator.get_ami_info(image1_id)
            image2 = self.comparator.get_ami_info(image2_id)
        else:
            image1 = self.comparator.get_docker_info(image1_id)
            image2 = self.comparator.get_docker_info(image2_id)
        
        # Print comparison
        self._print_comparison_header(image1, image2)
        self._print_size_comparison(image1, image2)
        
        if detailed:
            print()
            self._print_detailed_analysis(image1_id, image2_id)
        
        print()
        self._print_recommendations(image1, image2)
    
    def _print_comparison_header(self, image1: ImageInfo, image2: ImageInfo):
        """Print header with basic image information."""
        print("=" * 70)
        print("IMAGE COMPARISON")
        print("=" * 70)
        print()
        
        print(f"Image 1: {image1.id}")
        if 'name' in image1.metadata:
            print(f"  Name: {image1.metadata['name']}")
        print(f"  Created: {image1.creation_date}")
        print()
        
        print(f"Image 2: {image2.id}")
        if 'name' in image2.metadata:
            print(f"  Name: {image2.metadata['name']}")
        print(f"  Created: {image2.creation_date}")
        print()
    
    def _print_size_comparison(self, image1: ImageInfo, image2: ImageInfo):
        """Print size comparison."""
        print("SIZE COMPARISON")
        print("-" * 70)
        
        print(f"Image 1: {image1.size_gb:.2f} GB ({image1.size_mb:.0f} MB)")
        print(f"Image 2: {image2.size_gb:.2f} GB ({image2.size_mb:.0f} MB)")
        print()
        
        size_diff = image2.size_bytes - image1.size_bytes
        size_diff_mb = size_diff / (1024 * 1024)
        size_diff_gb = size_diff / (1024 * 1024 * 1024)
        
        if size_diff > 0:
            percent_increase = (size_diff / image1.size_bytes) * 100
            print(f"📈 Image 2 is LARGER by {size_diff_gb:.2f} GB ({size_diff_mb:.0f} MB)")
            print(f"   Size increase: {percent_increase:.1f}%")
        elif size_diff < 0:
            percent_decrease = (abs(size_diff) / image1.size_bytes) * 100
            print(f"📉 Image 2 is SMALLER by {abs(size_diff_gb):.2f} GB ({abs(size_diff_mb):.0f} MB)")
            print(f"   Size decrease: {percent_decrease:.1f}%")
        else:
            print("✅ Images are the same size")
    
    def _print_detailed_analysis(self, image1_id: str, image2_id: str):
        """Print detailed layer/component analysis."""
        print("DETAILED ANALYSIS")
        print("-" * 70)
        
        if self.image_type == 'docker':
            layers1 = self.comparator.get_layer_details(image1_id)
            layers2 = self.comparator.get_layer_details(image2_id)
            
            print(f"Image 1: {len(layers1)} layers")
            print(f"Image 2: {len(layers2)} layers")
            print()
            
            if layers2:
                print("Largest layers in Image 2:")
                sorted_layers = sorted(layers2, key=lambda l: l['size_bytes'], reverse=True)
                for layer in sorted_layers[:5]:
                    if layer['size_bytes'] > 0:
                        size_mb = layer['size_bytes'] / (1024 * 1024)
                        command = layer['command'][:60] + '...' if len(layer['command']) > 60 else layer['command']
                        print(f"  {size_mb:>8.1f} MB: {command}")
    
    def _print_recommendations(self, image1: ImageInfo, image2: ImageInfo):
        """Print optimization recommendations."""
        print("RECOMMENDATIONS")
        print("-" * 70)
        
        size_diff = image2.size_bytes - image1.size_bytes
        size_diff_mb = abs(size_diff) / (1024 * 1024)
        
        if size_diff > 100 * 1024 * 1024:  # > 100MB increase
            print(f"⚠️  Significant size increase detected ({size_diff_mb:.0f} MB)")
            print()
            print("Recommended actions:")
            print("  1. Review recent changes for unnecessary packages or files")
            print("  2. Check for leftover build artifacts or caches")
            print("  3. Verify cleanup scripts executed successfully")
            print("  4. Consider multi-stage build approach")
            
            if self.image_type == 'docker':
                print("  5. Run 'docker history' to identify large layers")
                print("  6. Use dive tool for detailed layer analysis")
        elif size_diff < -100 * 1024 * 1024:  # > 100MB decrease
            print(f"✅ Excellent! Size reduced by {size_diff_mb:.0f} MB")
            print()
            print("This optimization achieved significant space savings.")
        else:
            print("✅ Size change is minimal")
            print()
            print("Consider these general optimizations:")
            print("  • Use --no-install-recommends for apt packages")
            print("  • Clean package manager caches")
            print("  • Remove documentation and man pages")
            print("  • Strip debug symbols from binaries")


def main():
    parser = argparse.ArgumentParser(
        description='Compare Packer build artifacts to identify size changes'
    )
    parser.add_argument('image1', help='First image ID or reference')
    parser.add_argument('image2', help='Second image ID or reference')
    parser.add_argument('--type', choices=['ami', 'docker'], required=True,
                       help='Type of images to compare')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed layer/component analysis')
    
    args = parser.parse_args()
    
    comparator = ImageComparator(args.type)
    comparator.compare(args.image1, args.image2, detailed=args.detailed)


if __name__ == '__main__':
    main()
