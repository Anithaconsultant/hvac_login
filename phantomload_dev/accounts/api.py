from datetime import datetime
from num2words import num2words
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model, authenticate
from .models import UserGameProgress
from django.template.response import TemplateResponse
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, GameProgressSerializer
import pandas as pd
import os
import csv
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({
                "status": "error",
                "message": "Invalid credentials"
            }, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.user
        refresh = RefreshToken.for_user(user)

        return Response({
            "status": "success",
            "user": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        })


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "message": "User created successfully. Please check your email for verification."
        }, status=status.HTTP_201_CREATED)


logger = logging.getLogger(__name__)


class GameProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Add user to request data
            request.data['user'] = request.user.id
            serializer = GameProgressSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": "success",
                    "message": "Game progress saved successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)

            return Response({
                "status": "error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error saving game progress: {str(e)}")
            return Response({
                "status": "error",
                "message": "Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClientLoginView(APIView):
    """
    Custom login view for client authentication.
    """

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return Response({'detail': 'User not registered.'}, status=status.HTTP_404_NOT_FOUND)

        user = authenticate(request, email=username, password=password)

        if user is not None:
            if user.is_active:
                # Generate tokens manually
                refresh = RefreshToken.for_user(user)
                return Response({
                    'status': 'success',
                    'user_id': user.id,
                    'email': user.email,
                    'username': user.nickname,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'User account is disabled.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'detail': 'Invalid password.'}, status=status.HTTP_401_UNAUTHORIZED)
        # if user is not None and user.is_active:
        #     refresh = RefreshToken.for_user(user)
        #     token_data = {
        #         'status': 'success',
        #         'user_id': user.id,
        #         'email': user.email,
        #         'username': user.nickname,
        #         'tokens': {
        #             'access': str(refresh.access_token),
        #             'refresh': str(refresh)
        #         }
        #     }
        #     return TemplateResponse(request, 'home.html', token_data)
        # elif user is not None and not user.is_active:
        #     return Response({'detail': 'User account is disabled.'}, status=status.HTTP_403_FORBIDDEN)
        # else:
        #     return Response({'detail': 'Invalid password.'}, status=status.HTTP_401_UNAUTHORIZED)


class UserDataView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            return Response({
                'user_id': user.id,
                'email': user.email,
                'username': user.username,
                'user_data': user.user_data,
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user_data = request.data.get('user_data')
            if user_data is None:
                return Response({'detail': 'user_data is required.'}, status=status.HTTP_400_BAD_REQUEST)

            user.user_data = user_data
            user.save()

            return Response({'detail': 'User data updated successfully.'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

# class ReadExcelStaticView(APIView):
#     """
#     Reads a CSV file from staticfiles/docs and returns only columns H, J, K, L, M, N, and O as JSON.
#         """


#     def get(self, request):
#         filename = request.query_params.get('filename')
#         if not filename:
#             return Response({'error': 'Filename parameter is required.'}, status=400)

#         if '/' in filename or '\\' in filename:
#             return Response({'error': 'Invalid filename.'}, status=400)

#         csv_path = os.path.join(settings.BASE_DIR, 'staticfiles/docs', filename)

#         if not os.path.exists(csv_path):
#             return Response({'filename': filename, 'path': csv_path, 'error': 'File not found.'}, status=404)

#         try:
#             required_headers = [
#                'HotSpotID',
#                 'Power',
#                 'No_of_hours',
#                 'Standby_power',
#                 'Standby_hours',
#                 'Quanitity_of_fixtures',
#                 'Diversity_Factor',
#                 'ActiveZone'
#             ]

#             data = []
#             encodings_to_try = ['utf-8-sig', 'utf-16', 'latin1']

#             for enc in encodings_to_try:
#                 try:
#                     with open(csv_path, newline='', encoding=enc) as csvfile:
#                         reader = csv.DictReader(csvfile)

#                         # Check for missing columns
#                         missing = [h for h in required_headers if h not in reader.fieldnames]
#                         if missing:
#                             return Response({'error': f'Missing columns: {", ".join(missing)}'}, status=400)

#                         for row in reader:
#                             filtered = {h: row[h] for h in required_headers}
#                             data.append(filtered)

#                     # If we reached here, reading succeeded
#                     break

#                 except UnicodeDecodeError:
#                     data = []
#                     continue

#             if not data:
#                 return Response({'error': 'Unable to read CSV with supported encodings.'}, status=500)

#             return Response(data)

#         except Exception as e:
#             return Response({'error': str(e)}, status=500)


class ReadExcelAttemptView(APIView):
    EXCEL_FILENAME = "Energy Bill Data Table model.xlsx"

    def get(self, request):
        attempt = request.query_params.get('attempt')

        if not attempt:
            return Response({'error': 'Attempt parameter is required.'}, status=400)

        try:
            attempt_num = int(attempt)
        except ValueError:
            return Response({'error': 'Attempt must be an integer.'}, status=400)

        # --- File Path ---
        excel_path = os.path.join(
            settings.BASE_DIR, 'staticfiles/docs/Task02', self.EXCEL_FILENAME)
        if not os.path.exists(excel_path):
            return Response({'error': f'File not found: {excel_path}'}, status=404)

        try:
            xls = pd.ExcelFile(excel_path)
            sheet_names = xls.sheet_names
            sheet_index = attempt_num - 1

            if sheet_index < 0 or sheet_index >= len(sheet_names):
                return Response({
                    'error': f'Invalid attempt number. File has {len(sheet_names)} sheets.',
                    'available_sheets': sheet_names
                }, status=400)

            # --- Read the required sheet ---
            df = pd.read_excel(xls, sheet_name=sheet_names[sheet_index])
            df = df.dropna(how='all').fillna("")

            # --- Convert Net Payable Amount to Words ---
            amount_col = "Net payable amount  (₹)"
            words_col = "Net payable amount in words"

            if amount_col in df.columns and words_col in df.columns:
                for idx, row in df.iterrows():
                    amount_value = row[amount_col]
                    if isinstance(amount_value, (int, float)) and amount_value != 0:
                        rupees = int(amount_value)
                        paise = round((amount_value - rupees) * 100)
                        words = num2words(
                            rupees, lang='en_IN').title() + " Rupees"
                        if paise:
                            words += f" and {num2words(paise, lang='en_IN').title()} Paise"
                        words += " Only"
                        df.at[idx, words_col] = words

            # --- Fix Date Formatting (avoids NaTType error) ---
            for col in df.columns:
                if "date" in col.lower():
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    df[col] = df[col].apply(lambda x: x.strftime(
                        "%d/%m/%Y") if pd.notnull(x) else "")

            # --- Restrict Decimal Precision to 6 Digits ---
            float_cols = df.select_dtypes(include=["float", "float64"]).columns
            df[float_cols] = df[float_cols].apply(lambda x: x.round(6))

            # --- Convert DataFrame to JSON ---
            data = df.to_dict(orient='records')

            return Response({
                'filename': self.EXCEL_FILENAME,
                'sheet_name': sheet_names[sheet_index],
                'total_sheets': len(sheet_names),
                'row_count': len(data),
                'data': data
            })

        except Exception as e:
            return Response({'error': str(e)}, status=500)


# class FilterCSVDataTask09(APIView):
#     """
#     Reads five CSV files (Mask + 4 data files) based on the given attempt number.
#     Skips cells where the mask has False, and combines all four data files row-wise.
#     """

#     def get(self, request):
#         attempt = request.query_params.get("attempt")
#         if not attempt:
#             return Response({"error": "Attempt parameter is required."}, status=400)

#         try:
#             attempt_num = int(attempt)
#         except ValueError:
#             return Response({"error": "Attempt must be an integer."}, status=400)

#         base_dir = os.path.join(settings.BASE_DIR, "staticfiles", "docs/Task09")

#         # Define dynamic file names
#         files = {
#             "mask": f"PL_L1_TASK09_TF_Mask_Attempt{attempt_num}.csv",
#             "sources": f"PL_L1_TASK09_Sources_Attempt{attempt_num}.csv",
#             "points": f"PL_L1_TASK09_Points_Attempt{attempt_num}.csv",
#             "name_value": f"PL_L1_TASK09_Name_Value_Attempt{attempt_num}.csv",
#             "destinations": f"PL_L1_TASK09_Destinations_Attempt{attempt_num}.csv",
#         }

#         # Validate existence of all files
#         for key, fname in files.items():
#             fpath = os.path.join(base_dir, fname)
#             if not os.path.exists(fpath):
#                 return Response({"error": f"File not found: {fname}"}, status=404)

#         try:
#             # Load mask
#             mask_df = pd.read_csv(os.path.join(base_dir, files["mask"])).fillna(False)
#             # Convert truthy values to actual bools
#             mask_df = mask_df.map(
#                 lambda x: str(x).strip().lower() in ["true", "1", "yes"]
#                 if pd.notna(x)
#                 else False
#             )

#             # Load data CSVs
#             dataframes = {
#                 name: pd.read_csv(os.path.join(base_dir, fname)).fillna("")
#                 for name, fname in files.items()
#                 if name != "mask"
#             }

#             # Align mask and data dimensions
#             max_rows = len(mask_df)
#             max_cols = len(mask_df.columns)

#             # Combine data row-wise
#             combined_data = []
#             for i in range(max_rows):
#                 combined_record = {"row": i + 1}
#                 for sheet_name, df in dataframes.items():
#                     record = {}
#                     # Ensure row index exists
#                     if i < len(df):
#                         for j in range(min(len(df.columns), max_cols)):
#                             if bool(mask_df.iloc[i, j]):  # include only True mask cells
#                                 col_name = df.columns[j]
#                                 record[col_name] = df.iloc[i, j]
#                     combined_record[sheet_name] = record
#                 combined_data.append(combined_record)

#             return Response(
#                 {
#                     "attempt": attempt_num,
#                     "files": {k: v for k, v in files.items()},
#                     "total_rows": len(combined_data),
#                     "data": combined_data,
#                 }
#             )

#         except Exception as e:
#             return Response({"error": str(e)}, status=500)


class FilterCSVDataTask09(APIView):
    """
    Reads 5 CSV files (mask + 4 data files) based on attempt number.
    Filters cells using TF_Mask and merges matching keys across sheets into combined JSON.
    Keeps common fields once and merges other columns by sheet.
    """

    def get(self, request):
        attempt = request.query_params.get("attempt")
        if not attempt:
            return Response({"error": "Attempt parameter is required."}, status=400)

        try:
            attempt_num = int(attempt)
        except ValueError:
            return Response({"error": "Attempt must be an integer."}, status=400)

        base_dir = os.path.join(settings.BASE_DIR, "staticfiles", "docs", "Task09")

        # Define filenames
        files = {
            "mask": f"PL_L1_TASK09_TF_Mask_Attempt{attempt_num}.csv",
            "sources": f"PL_L1_TASK09_Sources_Attempt{attempt_num}.csv",
            "points": f"PL_L1_TASK09_Points_Attempt{attempt_num}.csv",
            "name_value": f"PL_L1_TASK09_Name_Value_Attempt{attempt_num}.csv",
            "destinations": f"PL_L1_TASK09_Destinations_Attempt{attempt_num}.csv",
        }

        # Validate file existence
        for key, fname in files.items():
            if not os.path.exists(os.path.join(base_dir, fname)):
                return Response({"error": f"File not found: {fname}"}, status=404)

        try:
            # --- Load Mask CSV safely ---
            mask_path = os.path.join(base_dir, files["mask"])
            mask_df = pd.read_csv(mask_path)
            mask_df = mask_df.fillna(False).infer_objects(copy=False)
            mask_df = mask_df.map(
                lambda x: str(x).strip().lower() in ["true", "1", "yes"]
                if pd.notna(x)
                else False
            )

            # --- Load the 4 data CSVs ---
            dataframes = {
                name: pd.read_csv(os.path.join(base_dir, fname)).fillna("")
                for name, fname in files.items()
                if name != "mask"
            }

            # --- Define common fields (appear once) ---
            common_fields = [
                "Game Level",
                "Task #",
                "Floor",
                "Room ID",
                "Room",
                "Equipment",
                "HotSpotID",
                "ActiveZone",
            ]

            # --- Get max rows dynamically ---
            max_rows = max(len(df) for df in dataframes.values())
            max_cols = min(len(mask_df.columns), max(len(df.columns) for df in dataframes.values()))

            merged_data = []

            for i in range(max_rows):
                row_record = {"row": i + 1}
                temp_dict = {}
                has_valid_data = False

                for sheet_name, df in dataframes.items():
                    if i >= len(df):
                        continue

                    for j in range(min(len(df.columns), max_cols)):
                        try:
                            mask_value = bool(mask_df.iloc[i, j])
                        except Exception:
                            mask_value = False

                        if not mask_value:
                            continue

                        col_name = str(df.columns[j]).strip()
                        value = df.iloc[i, j]

                        if str(value).strip() == "":
                            continue

                        # Convert points values to integer safely
                        if sheet_name == "points":
                            try:
                                if isinstance(value, (int, float, str)) and str(value).strip():
                                    value = int(float(value))
                            except ValueError:
                                pass  # Ignore if not convertible

                        # --- Common fields only once ---
                        if col_name in common_fields:
                            if col_name not in row_record:
                                row_record[col_name] = value
                            continue

                        # --- Initialize dict for each column if not exists ---
                        if col_name not in temp_dict:
                            temp_dict[col_name] = {
                                "Sources": [],
                                "Points": [],
                                "Name_Value": [],
                                "Destinations": [],
                            }

                        # --- Map sheet names properly ---
                        sheet_key_map = {
                            "sources": "Sources",
                            "points": "Points",
                            "name_value": "Name_Value",
                            "destinations": "Destinations",
                        }
                        sheet_key = sheet_key_map.get(sheet_name, sheet_name.capitalize())

                        # --- Append value safely ---
                        if sheet_key in temp_dict[col_name]:
                            temp_dict[col_name][sheet_key].append(value)
                        else:
                            temp_dict[col_name][sheet_key] = [value]

                        has_valid_data = True

                # --- Clean up empty lists ---
                for key, val in temp_dict.items():
                    cleaned = {k: v for k, v in val.items() if v}
                    if cleaned:
                        row_record[key] = cleaned

                # --- Add non-empty rows only ---
                if has_valid_data:
                    merged_data.append(row_record)

            return Response(
                {
                    "attempt": attempt_num,
                    "files": files,
                    "total_rows": len(merged_data),
                    "data": merged_data,
                },
                status=200,
            )

        except Exception as e:
            print("❌ ERROR in FilterCSVDataTask09:", str(e))
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=500)
