import random
from num2words import num2words
from rest_framework_simplejwt.views import (
    TokenObtainPairView
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model, authenticate
from .serializers import  RegisterSerializer, GameProgressSerializer
import pandas as pd
import os
from django.conf import settings
import logging
from num2words import num2words
from rest_framework.decorators import api_view
from .models import ActiveSession,LoadShredderRecord,UserGameProgress
from .utils import can_user_login
import uuid
from django.db import transaction

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

@api_view(['POST'])
def unity_logout(request):
    session_key = request.data.get("session_key")

    if not session_key:
        return Response({"error": "session_key is required"}, status=400)

    ActiveSession.objects.filter(session_key=session_key).delete()

    return Response({"message": "Logged out successfully"})


class ClientLoginView(APIView):

    def post(self, request):

        username = request.data.get('username')
        password = request.data.get('password')

        try:
            db_user = User.objects.get(email=username)

        except User.DoesNotExist:
            return Response(
                {'detail': 'User not registered.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = authenticate(
            request,
            username=db_user.email,
            password=password
        )

        print("AUTH USER:", user)

        if user is None:
            return Response(
                {'detail': 'Invalid password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'detail': 'User account is disabled.'},
                status=status.HTTP_403_FORBIDDEN
            )

        allowed, error = can_user_login(user)

        print("allowed:", allowed)

        if not allowed:
            return Response({
                'detail': 'Maximum users reached. Try later.'
            }, status=status.HTTP_403_FORBIDDEN)

        session_key = str(uuid.uuid4())

        print("CREATING SESSION")

        obj, created = ActiveSession.objects.update_or_create(
            user=user,
            defaults={"session_key": session_key}
        )

        print("SESSION CREATED:", obj.id)

        refresh = RefreshToken.for_user(user)

        return Response({
            'allowed':allowed,
            'status': 'success',
            'user_id': user.id,
            'email': user.email,
            'username': user.nickname,
            'session_key': session_key,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_200_OK)

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

class ReadExcelAttemptView(APIView):
    EXCEL_FILENAME = "energy_bill_data_table_model.xlsx"

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
             
                'data': data
            })

        except Exception as e:
            return Response({'error': str(e)}, status=500)


class Task11TicketFixesApi(APIView):

    def get(self, request):
        file_name = "PL_L1_TASK11_Tickets_Fixes_Data_API.csv"
        csv_path = os.path.join(
            settings.BASE_DIR, "staticfiles/docs/Task11", file_name
        )

        if not os.path.exists(csv_path):
            return Response(
                {"error": "CSV file not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            df = pd.read_csv(csv_path, encoding="utf-8")

            # Convert dataframe to records first
            records = df.to_dict(orient="records")

            cleaned_data = []

            for row in records:
                cleaned_row = {}

                for key, value in row.items():

                    # 🔴 CRITICAL FIX: handle NaN properly
                    if pd.isna(value):
                        continue

                    if isinstance(value, str):
                        value = value.strip()
                        if value.lower() in ("", "na", "nan", "null"):
                            continue

                    cleaned_row[key] = value

                if cleaned_row:
                    cleaned_data.append(cleaned_row)

            return Response(
                {
                    "count": len(cleaned_data),
                    "data": cleaned_data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class Task11LightingScenarioApi(APIView):

    def get(self, request):
        file_name = "PL_L1_TASK11_SF_Z25_Lighting_Scenario_Data_API.csv"
        csv_path = os.path.join(
            settings.BASE_DIR, "staticfiles/docs/Task11", file_name
        )

        if not os.path.exists(csv_path):
            return Response(
                {"error": "CSV file not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            df = pd.read_csv(csv_path, encoding="utf-8")

            # Convert dataframe to records first
            records = df.to_dict(orient="records")

            cleaned_data = []

            for row in records:
                cleaned_row = {}

                for key, value in row.items():

                    # 🔴 CRITICAL FIX: handle NaN properly
                    if pd.isna(value):
                        continue

                    if isinstance(value, str):
                        value = value.strip()
                        if value.lower() in ("", "na", "nan", "null"):
                            continue

                    cleaned_row[key] = value

                if cleaned_row:
                    cleaned_data.append(cleaned_row)

            return Response(
                {
                    "count": len(cleaned_data),
                    "data": cleaned_data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class Task11LightFixtureApi(APIView):

    def get(self, request):
       

        # -------------------------------------------------------------------
        # Validate attempt parameter
        # -------------------------------------------------------------------
        attempt = request.query_params.get("attempt")
        if not attempt:
            return Response({"error": "Attempt parameter is required."}, status=400)

        try:
            attempt_num = int(attempt)
        except ValueError:
            return Response({"error": "Attempt must be an integer."}, status=400)

        base_dir = os.path.join(settings.BASE_DIR, "staticfiles", "docs", "Task11")

        # -------------------------------------------------------------------
        # CSV file definitions
        # -------------------------------------------------------------------
        files = {
            "mask": f"PL_L1_TASK11_LightFixtureAPI_TF_Masks_Attempt{attempt_num}.csv",
            "sources": f"PL_L1_TASK11_LightFixtureAPI_Sources_Attempt{attempt_num}.csv",
            "points": f"PL_L1_TASK11_LightFixtureAPI_Points_Attempt{attempt_num}.csv",
            "name_value": f"PL_L1_TASK11_LightFixtureAPI_Name_Value_Attempt{attempt_num}.csv",
            "destinations": f"PL_L1_TASK11_LightFixtureAPI_Destinations_Attempt{attempt_num}.csv",
        }

        # -------------------------------------------------------------------
        # Check file existence
        # -------------------------------------------------------------------
        for fname in files.values():
            if not os.path.exists(os.path.join(base_dir, fname)):
                return Response({"error": f"File not found: {fname}"}, status=404)

        try:
            # -------------------------------------------------------------------
            # Load TF Mask CSV (SOURCE OF TRUTH)
            # -------------------------------------------------------------------
            mask_df = pd.read_csv(os.path.join(base_dir, files["mask"]))
            mask_df = mask_df.fillna('').infer_objects(copy=False)
            mask_df = mask_df.map(
                lambda x: str(x).strip().lower() in ["true", "1", "yes"]
                if pd.notna(x)
                else False
            )

            # -------------------------------------------------------------------
            # Load other CSVs
            # -------------------------------------------------------------------
            dataframes = {
                name: pd.read_csv(os.path.join(base_dir, fname)).fillna("")
                for name, fname in files.items()
                if name != "mask"
            }

            # -------------------------------------------------------------------
            # Fields removed completely
            # -------------------------------------------------------------------
            removed_fields = {
                "GameLevel",
                "TaskNo",
            }

            # -------------------------------------------------------------------
            # Fields allowed ONLY when masked true
            # -------------------------------------------------------------------
            conditional_common_fields = {
                "Floor",
                "RoomID",
                "RoomName",
                "Equipment",
                "HotSpotID",
                "IsActiveZone",
            }

            merged_data = []

            max_rows = max(len(df) for df in dataframes.values())
            max_cols = min(
                len(mask_df.columns),
                max(len(df.columns) for df in dataframes.values())
            )

            # -------------------------------------------------------------------
            # MERGING LOOP
            # -------------------------------------------------------------------
            for i in range(max_rows):

                row_record = {"row": i + 1}
                temp_dict = {}
                has_valid_data = False

                for sheet_name, df in dataframes.items():

                    if i >= len(df):
                        continue

                    for j in range(min(len(df.columns), max_cols)):

                        # Mask check
                        if i >= len(mask_df) or not bool(mask_df.iloc[i, j]):
                            continue

                        col_name = str(df.columns[j]).strip()
                        value = df.iloc[i, j]

                        if str(value).strip() == "":
                            continue

                        # Convert points
                        if sheet_name == "points":
                            try:
                                value = int(float(value))
                            except:
                                pass

                        # ❌ Skip removed fields always
                        if col_name in removed_fields:
                            continue

                        # ✅ Conditional common fields (only if masked true)
                        if col_name in conditional_common_fields:

                            if col_name == "IsActiveZone":
                                row_record["IsActiveZone"] = True
                            else:
                                row_record[col_name] = value

                            has_valid_data = True
                            continue

                        # -------------------------------------------------------------------
                        # Normal merged fields
                        # -------------------------------------------------------------------
                        if col_name not in temp_dict:
                            temp_dict[col_name] = {}

                        sheet_key = {
                            "sources": "Sources",
                            "points": "Points",
                            "name_value": "Name_Value",
                            "destinations": "Destinations",
                        }.get(sheet_name)

                        # Convert value properly
                        if sheet_name == "points":
                            try:
                                value = int(float(value))
                            except:
                                pass

                        if sheet_name == "name_value":
                            value = str(value)  # ALWAYS string

                        temp_dict[col_name][sheet_key] = value
                        has_valid_data = True

                # Add merged columns
                for key, val in temp_dict.items():
                    if val:
                        row_record[key] = val

                if has_valid_data:
                    merged_data.append(row_record)

            # -------------------------------------------------------------------
            # Response
            # -------------------------------------------------------------------
            return Response(
                {
                    "data": merged_data
                },
                status=200,
            )

        except Exception as e:
            print("❌ ERROR:", str(e))
            return Response({"error": str(e)}, status=500)
        
class ReadQandAexcel(APIView):
    EXCEL_FILENAME = "PL_API Inputs_QA_Feature.xlsx"

    def get(self, request):

        user_id = request.GET.get('user_id')

        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        # ✅ Get user gender
        try:
            gender = User.objects.filter(id=user_id).values_list('gender', flat=True).first()
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # (optional) progress data if needed later
        progress_data = UserGameProgress.objects.filter(user_id=user_id)

        # --- File Path ---
        excel_path = os.path.join(
            settings.BASE_DIR, 'staticfiles/docs/', self.EXCEL_FILENAME
        )

        if not os.path.exists(excel_path):
            return Response(
                {'error': f'File not found: {excel_path}'},
                status=404
            )

        try:
            df = pd.read_excel(excel_path)
            df = df.dropna(how='all').fillna("")
            data = df.to_dict(orient='records')

            return Response({
                'gender': gender,   # ✅ added here
                'data': data
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=500
            )


class ReadTask08excel(APIView):
    EXCEL_FILENAME = "L1_T08_API data.xlsx"

    def get(self, request):

        excel_path = os.path.join(
            settings.BASE_DIR,
            'staticfiles/docs/Task08/',
            self.EXCEL_FILENAME
        )

        if not os.path.exists(excel_path):
            return Response(
                {'error': f'File not found: {excel_path}'},
                status=404
            )

        try:
            # --- Read Excel ---
            df = pd.read_excel(excel_path)
            df = df.dropna(how='all').fillna("")

            # --- Normalize column names ---
            df.columns = df.columns.str.strip().str.lower()

            # --------------------------------------------------
            # Convert correct answer columns to INT (1 / 0)
            # --------------------------------------------------
            correct_cols = [
                'iscorrectanswer',
                'iscorrectanswer.1',
                'iscorrectanswer.2',
                'iscorrectanswer.3'
            ]

            for col in correct_cols:
                if col in df.columns:

                    df[col] = pd.to_numeric(df[col], errors='coerce')

                    df[col] = df[col].apply(
                        lambda x: int(x) if pd.notna(x) else None
                    )

            # --------------------------------------------------
            # Convert Y and Z columns to FLOAT
            # --------------------------------------------------
            float_cols = ['initialsetpointtemp', 'initialroomtemp']

            for col in float_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)

            # --- Validate required columns ---
            if 'zoneid' not in df.columns or 'active' not in df.columns:
                return Response(
                    {
                        'error': 'Required columns missing after normalization',
                        'columns_found': df.columns.tolist()
                    },
                    status=400
                )

            # --- Normalize active column safely ---
            df['active'] = (
                df['active']
                .astype(str)
                .str.strip()
                .str.upper()
            )

            # ================= RANDOMIZATION LOGIC =================
            for zone_id in df['zoneid'].unique():

                zone_rows = df[df['zoneid'] == zone_id]

                false_rows = zone_rows[
                    zone_rows['active'].str.startswith('FALSE_')
                ]

                for false_value in false_rows['active'].unique():

                    group = false_rows[
                        false_rows['active'] == false_value
                    ]

                    try:
                        _, counts = false_value.split('_')
                        select_count, _ = map(int, counts.split('/'))
                    except ValueError:
                        continue

                    if select_count <= 0 or len(group) < select_count:
                        continue

                    selected_indices = random.sample(
                        list(group.index),
                        select_count
                    )

                    not_selected_indices = list(
                        set(group.index) - set(selected_indices)
                    )

                    df.loc[selected_indices, 'active'] = 'TRUE'
                    df.loc[not_selected_indices, 'active'] = 'FALSE'
            # =======================================================

            # --- Send ONLY TRUE rows ---
            df_true = df[
                df['active'] == 'TRUE'
            ].copy()

            # --- Remove first 2 columns ---
            df_true = df_true.iloc[:, 2:]

            # --- Remove 'active' column from response ---
            if 'active' in df_true.columns:
                df_true = df_true.drop(columns=['active'])

            # --- Remove empty / NA / "Null" values and keys ---
            cleaned_data = []

            for _, row in df_true.iterrows():

                row_dict = {}

                for key, value in row.items():

                    if (
                        value not in ["", None]
                        and not pd.isna(value)
                        and str(value).strip().lower() != "null"
                    ):

                        # FIX: ensure iscorrectanswer values are INT not FLOAT
                        if "iscorrectanswer" in key:
                            value = int(value)

                        row_dict[key] = value

                cleaned_data.append(row_dict)

            return Response({
                'data': cleaned_data
            })

        except Exception as e:
            import traceback
            return Response(
                {
                    'error': str(e),
                    'trace': traceback.format_exc()
                },
                status=500
            )
            
def get_username_from_email(email):
    try:
        user = User.objects.get(email=email)
        print(user)
        return user.first_name+' '+user.last_name
    except User.DoesNotExist:
        return None
    
@api_view(['POST'])
def get_username(request):
    email = request.data.get('email')
    print(email)
    username = get_username_from_email(email)
    print(username)
    return Response({
        "username": username
    })
    
@api_view(['GET'])
def get_userprogress(request):

    user_id = request.GET.get('user_id')

    if not user_id:
        return Response({"error": "user_id is required"}, status=400)

    progress_data = UserGameProgress.objects.filter(
        user_id=user_id
    ).exclude(
        completion_status="not_started"
    ).order_by('level', 'attempt_number', 'task_number').values()

    return Response({
        "data": list(progress_data)
    })

User = get_user_model()


@api_view(['GET'])
def get_loadshredder_data(request):
    user_id = request.GET.get('user_id')

    if not user_id:
        return Response({"error": "user_id is required"}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    records = LoadShredderRecord.objects.filter(user=user).exclude(
        status="not_started"
    ).order_by('actual_attempt_number')

    data = []
    for record in records:
        data.append({
            "actual_attempt_number":int(record.actual_attempt_number),
            "attempt_number": record.attempt_number,
            "place": record.place,
            "starting_case": int(record.starting_case) if record.starting_case not in [None, ''] else 0,
            "current_sf_tr": int(record.current_sf_tr) if record.current_sf_tr not in [None, ''] else 0,
            "status": record.status,
            "score": record.score,
        })

    return Response({
        "data": data
    })
    
    
@api_view(['POST'])
def save_loadshredder_full(request):
    data = request.data
    email = data.get('email')

    if not email:
        return Response({"error": "email is required"}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    # 🔒 ensure both tables update together
    with transaction.atomic():

        # =========================
        # ✅ STEP 1: Calculate attempt
        # =========================
        last_attempt = LoadShredderRecord.objects.filter(user=user).order_by('-actual_attempt_number').first()

        if last_attempt:
            actual_attempt_number = last_attempt.actual_attempt_number + 1
        else:
            actual_attempt_number = 1

        attempt_number = ((actual_attempt_number - 1) % 3) + 1

        # =========================
        # ✅ STEP 2: Update LoadShredderRecord
        # =========================
        existing_record = LoadShredderRecord.objects.filter(
            user=user,
            attempt_number=attempt_number
        ).first()

        if existing_record:
            existing_record.actual_attempt_number = actual_attempt_number
            existing_record.place = data.get('place')
            existing_record.starting_case = data.get('starting_case')
            existing_record.current_sf_tr = data.get('current_sf_tr')
            existing_record.status = data.get('status')
            existing_record.score = data.get('score')
            existing_record.save()
        else:
            LoadShredderRecord.objects.create(
                user=user,
                attempt_number=attempt_number,
                actual_attempt_number=actual_attempt_number,
                place=data.get('place'),
                starting_case=data.get('starting_case'),
                current_sf_tr=data.get('current_sf_tr'),
                status=data.get('status'),
                score=data.get('score')
            )

        # =========================
        # ✅ STEP 3: Update UserGameProgress (SYNCED)
        # =========================
        attempt_row = UserGameProgress.objects.filter(
            user=user,
            level=1,
            task_number="Load_Shredder",
            attempt_number=attempt_number
        ).first()

        if attempt_row:
            attempt_row.points_scored = data.get('score')
            attempt_row.completion_status = data.get('status')
            attempt_row.time_taken = data.get('time_taken')
            attempt_row.max_points = data.get('max_points', 100)
            attempt_row.hint_penalty_points = 0
            attempt_row.bonus_points = 0
            attempt_row.tools_earned = []
            attempt_row.badges = []
            attempt_row.super_powers = []
            attempt_row.save()

        else:
            return Response({
                "error": f"No matching progress row for attempt {attempt_number}"
            }, status=404)

    # =========================
    # ✅ FINAL RESPONSE
    # =========================
    return Response({
        "message": "Saved successfully in both tables",
        "attempt_used": attempt_number,
        "actual_attempt_number": actual_attempt_number
    })
    