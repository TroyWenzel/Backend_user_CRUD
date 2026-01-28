import yaml
import os

def merge_swagger_files():
    # Merge multiple swagger files into one comprehensive API documentation
    
    # Find the static directory
    possible_static_dirs = ['static', 'app/static', './static', './app/static']
    
    swagger_dir = None
    for dir_path in possible_static_dirs:
        if os.path.exists(dir_path):
            swagger_dir = dir_path
            break
    
    if not swagger_dir:
        return None
    
    # Create base structure
    base = {
        'swagger': '2.0',
        'info': {
            'title': 'Mechanic Shop API',
            'description': 'Complete API for managing mechanic shop operations including customers, mechanics, parts, inventory, and service tickets',
            'version': '1.0.0'
        },
        'host': 'https://api-application-factory-pattern.onrender.com',
        'schemes': ['https'],
        'consumes': ['application/json'],
        'produces': ['application/json'],
        'securityDefinitions': {
            'bearerAuth': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'Token authentication. Format: Bearer <token>'
            }
        },
        'paths': {},
        'definitions': {}
    }
    
    # Files to merge (in order)
    files_to_merge = [
        'customer_swagger.yaml',
        'mechanic_swagger.yaml',
        'parts_and_inventory_swagger.yaml',
        'service_tickets_swagger.yaml'
    ]
    
    for file in files_to_merge:
        file_path = os.path.join(swagger_dir, file)
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    additional = yaml.safe_load(f)
                
                # Merge paths
                if 'paths' in additional:
                    for path, methods in additional['paths'].items():
                        if path in base['paths']:
                            # Merge methods for existing path
                            base['paths'][path].update(methods)
                        else:
                            # Add new path
                            base['paths'][path] = methods
                
                # Merge definitions (avoid duplicates)
                if 'definitions' in additional:
                    for def_name, def_schema in additional['definitions'].items():
                        if def_name not in base['definitions']:
                            base['definitions'][def_name] = def_schema
            except:
                pass
    
    # Write merged file
    output_file = os.path.join(swagger_dir, 'mechanic_shop_swagger.yaml')
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(base, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except:
        return None
    
    return base

# Auto-run when imported
try:
    merged_swagger = merge_swagger_files()
except:
    merged_swagger = None