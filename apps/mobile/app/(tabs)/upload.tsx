import * as ImagePicker from 'expo-image-picker';
import { type Href, router } from 'expo-router';
import { useState } from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';

import type { UploadAsset } from '@/api/uploads';
import type { UploadVisibility } from '@/api/types';
import { useSession } from '@/auth/useSession';
import { ActionButton } from '@/components/ActionButton';
import { AuthRequired } from '@/components/AuthRequired';
import { ErrorState } from '@/components/ErrorState';
import { Screen } from '@/components/Screen';
import { StatusBadge } from '@/components/StatusBadge';
import { VisibilitySelector } from '@/components/VisibilitySelector';
import { createLocalJobId } from '@/features/jobs/jobStore';
import { useUploadImage } from '@/features/upload/useUploadImage';
import { useNetworkState } from '@/hooks/useNetworkState';
import { colors, radii, spacing, typography } from '@/theme/tokens';

function selectedAssetFromPicker(asset: ImagePicker.ImagePickerAsset): UploadAsset {
  return {
    fileName: asset.fileName,
    height: asset.height,
    mimeType: asset.mimeType,
    uri: asset.uri,
    width: asset.width,
  };
}

export default function UploadScreen() {
  const { user } = useSession();
  const { isOffline } = useNetworkState();
  const uploadMutation = useUploadImage();
  const [selectedAsset, setSelectedAsset] = useState<UploadAsset | null>(null);
  const [visibility, setVisibility] = useState<UploadVisibility>('private');
  const [pickerError, setPickerError] = useState<string | null>(null);

  if (!user) {
    return (
      <Screen title="Upload" subtitle="Sign in before sending private images to ingestion.">
        <AuthRequired action="upload images" />
      </Screen>
    );
  }

  async function pickFromLibrary() {
    setPickerError(null);
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();

    if (!permission.granted) {
      setPickerError('Photo library permission is required to select an image.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      allowsEditing: false,
      allowsMultipleSelection: false,
      mediaTypes: ['images'],
      quality: 0.92,
    });

    if (!result.canceled && result.assets[0]) {
      setSelectedAsset(selectedAssetFromPicker(result.assets[0]));
    }
  }

  async function takePhoto() {
    setPickerError(null);
    const permission = await ImagePicker.requestCameraPermissionsAsync();

    if (!permission.granted) {
      setPickerError('Camera permission is required to capture an image.');
      return;
    }

    try {
      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: false,
        mediaTypes: ['images'],
        quality: 0.92,
      });

      if (!result.canceled && result.assets[0]) {
        setSelectedAsset(selectedAssetFromPicker(result.assets[0]));
      }
    } catch (error) {
      setPickerError(error instanceof Error ? error.message : 'Camera capture failed.');
    }
  }

  async function submitUpload() {
    if (!selectedAsset || isOffline) {
      return;
    }

    const localId = createLocalJobId();

    try {
      const response = await uploadMutation.mutateAsync({
        asset: selectedAsset,
        localId,
        visibility,
      });
      setSelectedAsset(null);
      router.push(`/job/${encodeURIComponent(response.job_id)}` as Href);
    } catch {
      router.push(`/job/${encodeURIComponent(localId)}` as Href);
    }
  }

  return (
    <Screen title="Upload" subtitle="Pick a photo, choose visibility, and queue async ingestion.">
      {isOffline ? (
        <ErrorState
          title="Offline"
          message="Uploads pause while the device is offline. Reconnect and try again."
        />
      ) : null}

      <View style={styles.panel}>
        <View style={styles.panelHeader}>
          <Text style={styles.panelTitle}>Source</Text>
          <StatusBadge label={selectedAsset ? 'selected' : 'empty'} tone={selectedAsset ? 'success' : 'muted'} />
        </View>

        {selectedAsset ? (
          <Image source={{ uri: selectedAsset.uri }} resizeMode="cover" style={styles.preview} />
        ) : (
          <View style={styles.emptyPreview}>
            <Text style={styles.emptyPreviewTitle}>No image selected</Text>
            <Text style={styles.emptyPreviewCopy}>Choose from the library or use the camera.</Text>
          </View>
        )}

        <View style={styles.actions}>
          <ActionButton label="Photo library" onPress={pickFromLibrary} variant="secondary" />
          <ActionButton label="Camera" onPress={takePhoto} variant="secondary" />
        </View>

        {pickerError ? <Text style={styles.errorText}>{pickerError}</Text> : null}
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Visibility</Text>
        <VisibilitySelector value={visibility} onChange={setVisibility} />
      </View>

      <ActionButton
        disabled={!selectedAsset || isOffline || uploadMutation.isPending}
        label={uploadMutation.isPending ? 'Queueing...' : 'Upload for ingestion'}
        onPress={submitUpload}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  panel: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  panelHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  panelTitle: {
    color: colors.text,
    fontSize: typography.subtitle,
    fontWeight: '900',
  },
  preview: {
    aspectRatio: 1,
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.md,
    width: '100%',
  },
  emptyPreview: {
    alignItems: 'center',
    aspectRatio: 1,
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.md,
    gap: spacing.xs,
    justifyContent: 'center',
    padding: spacing.lg,
  },
  emptyPreviewTitle: {
    color: colors.text,
    fontSize: typography.subtitle,
    fontWeight: '900',
  },
  emptyPreviewCopy: {
    color: colors.muted,
    fontSize: typography.body,
    lineHeight: 22,
    textAlign: 'center',
  },
  actions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  errorText: {
    color: colors.danger,
    fontSize: typography.caption,
    lineHeight: 18,
  },
});
