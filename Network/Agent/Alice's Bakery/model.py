import json
import pandas as pd
from fastapi import HTTPException,status

class MarketAssistant:

    def __init__(self, name: str) -> None:
        """
        Initialize the MarketAssistant with a name and API key for OpenAI.
        """
        self.name = name
        # Load API key from configuration file (commented out if not needed for now)
        # with open('config.json') as config_file:
        #     config = json.load(config_file)
        #     self.api_key = config.get("api_key")

        # # Initialize OpenAI API
        # openai.api_key = self.api_key
        
    def sell(self, token: str, items: dict) -> dict:
        """
        Processes the sale of items. Validates the token, checks if items exist,
        reduces their stock, and returns a success message.

        Parameters
        ----------
        token : str
            Authorization token for the transaction.
        items : dict
            Dictionary containing items and their corresponding quantities to sell.

        Returns
        -------
        dict
            Dictionary containing the sold items and success message.

        Raises
        ------
        HTTPException
            Raised for invalid tokens, missing items, or insufficient stock.
        """
        
        # Check if items exist and token is valid
        if not self._item_exists(items):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more items do not exist or stock is insufficient.")
        
        if not self._is_token_valid(token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token provided.")
        
        # Load product data from CSV
        df_products = self._load_products()

        # Reduce stock of each item and update the CSV
        for product_name, quantity_sold in items.items():
                # Find the item in the DataFrame
                product_info = df_products[df_products['Product Name'] == product_name]
            
                # Reduce the stock
                available_stock = product_info['Number'].values[0]
                df_products.loc[df_products['Product Name'] == product_name, 'Number'] = available_stock - quantity_sold
                
            
        
        # Save the updated DataFrame back to CSV
        self._save_products(df_products)

        # Return success message with sold items
        return {"sold_items": items, "message": "Items sold successfully."}
        

    def _item_exists(self, items: dict) -> bool:
        """
        Checks if the requested items exist in the product catalog (CSV file) and 
        whether there is enough stock for each item.
        
        Parameters
        ----------
        items : dict
            Dictionary of items to check, where the key is the product name and the value is the quantity requested.
            
        Returns
        -------
        bool
            True if all items exist and have enough stock, False otherwise.
        
        Raises
        ------
        ValueError
            If any item does not exist or if the stock is insufficient.
        """
        df_products = self._load_products()

        for product_name, quantity_needed in items.items():
            # Check if the product exists
            product_info = df_products[df_products['Product Name'] == product_name]
            
            if product_info.empty:
                return False
            # Check if there is enough stock
            available_stock = product_info['Number'].values[0]
            if available_stock < quantity_needed:
                return False
        
        return True
    
    def _is_token_valid(self, token: str) -> bool:
        """
        Validates the token for the transaction.
        
        Parameters
        ----------
        token : str
            The token to validate.
            
        Returns
        -------
        bool
            True if the token is valid, False otherwise.
        """
        # Add token validation logic here
        return True

    def request(self, request: dict) -> dict:
        """
        Processes a product request and returns only products that can fulfill 
        the requested quantity, considering available stock.
        
        Parameters
        ----------
        request : dict
            A dictionary where the key is the product name (str) and the value is the quantity needed (int).
            Returns
    -------
    dict
        A dictionary where the key is the product name (str) and the value is the requested quantity (int),
        but only for products that exist in the CSV file and have enough stock.
    """
    
        # Load product data from the CSV file into a DataFrame
        df_products = self._load_products()
        
        # Initialize an empty dictionary to store the result
        result = {}
        
        # Iterate over each product and its required quantity from the request dictionary
        for product_name, quantity_needed in request.items():
            # Filter the DataFrame to find the product by name
            product_info = df_products[df_products['Product Name'] == product_name]
            
            # If the product is found (non-empty DataFrame)
            if not product_info.empty:
                # Check if the available stock is greater than or equal to the requested quantity
                print(product_info)
                available_stock = product_info['Number'].values[0]
                price_per_one = product_info['Price'].values[0]
                unit = product_info['Unit'].values[0]
                if available_stock >= quantity_needed:
                    # If enough stock is available, add the product and requested quantity to the result
                    result[product_name] = {"number":quantity_needed, "price":price_per_one,"unit":unit}
        
        # Return the dictionary containing the products and quantities requested that can be fulfilled
        return result

    def _load_products(self) -> pd.DataFrame:
        """
        Loads the product data from the CSV file into a Pandas DataFrame.
        
        Returns
        -------
        pd.DataFrame
            A DataFrame containing the product data from the CSV file.
        """
        
        # Specify the CSV file name (path to the file can be adjusted as necessary)
        file_name = 'products.csv'
        
        # Read the CSV file into a Pandas DataFrame and return it
        df = pd.read_csv(file_name)
        
        return df

    def _save_products(self, df: pd.DataFrame) -> None:
        """
        Saves the updated product data back to the CSV file.
        
        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame containing updated product data.
        """
        
        # Specify the CSV file name (path to the file can be adjusted as necessary)
        file_name = 'products.csv'
        
        # Save the DataFrame back to the CSV file
        df.to_csv(file_name, index=False)
